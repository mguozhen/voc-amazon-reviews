"""Unit tests for the MCP server tools.

All network calls are mocked: no Amazon scrapes, no Anthropic calls, no
Shulex API hits. Tests verify the wiring (arg validation, subprocess
construction, output parsing, error mapping) — they don't validate the
underlying shell scripts (those have their own tests in ../../tests/).

Run from the repo root:
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r mcp_server/requirements-dev.txt
    pytest mcp_server/tests/
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Tests live one level deeper than the package — add the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from mcp_server import tools  # noqa: E402
from mcp_server.schemas import ListingImprovements  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_REPORT = (FIXTURES / "sample_analyze_output.md").read_text()
SAMPLE_FETCH = json.loads((FIXTURES / "sample_fetch_output.json").read_text())


# ── helpers ─────────────────────────────────────────────────────────────

def _fake_completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(
        args=["bash"], returncode=returncode, stdout=stdout, stderr=stderr
    )


# ── _validate_asin ──────────────────────────────────────────────────────

class TestValidateAsin:
    def test_uppercase_valid(self):
        assert tools._validate_asin("B08N5WRWNW") == "B08N5WRWNW"

    def test_lowercase_normalized(self):
        assert tools._validate_asin("b08n5wrwnw") == "B08N5WRWNW"

    def test_whitespace_stripped(self):
        assert tools._validate_asin("  B08N5WRWNW  ") == "B08N5WRWNW"

    def test_wrong_length_rejected(self):
        with pytest.raises(ValueError, match="invalid ASIN"):
            tools._validate_asin("B08N5WRWN")  # 9 chars

    def test_special_chars_rejected(self):
        with pytest.raises(ValueError, match="invalid ASIN"):
            tools._validate_asin("B08N5-RWNW")

    def test_empty_rejected(self):
        with pytest.raises(ValueError, match="invalid ASIN"):
            tools._validate_asin("")


# ── _run_script ─────────────────────────────────────────────────────────

class TestRunScript:
    def test_returns_stdout_on_success(self):
        with patch("subprocess.run", return_value=_fake_completed(stdout="hello")):
            assert tools._run_script("fetch.sh", ["B08N5WRWNW"]) == "hello"

    def test_raises_on_nonzero_exit(self):
        with patch("subprocess.run",
                   return_value=_fake_completed(stderr="boom", returncode=1)):
            with pytest.raises(RuntimeError, match="fetch.sh failed"):
                tools._run_script("fetch.sh", ["B08N5WRWNW"])

    def test_truncates_long_stderr(self):
        with patch("subprocess.run",
                   return_value=_fake_completed(stderr="x" * 5000, returncode=1)):
            with pytest.raises(RuntimeError) as exc:
                tools._run_script("fetch.sh", [])
            # 600 cap on stderr in the message — full size never reaches MCP client.
            assert len(str(exc.value)) < 1500

    def test_timeout_maps_to_runtime_error(self):
        with patch("subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd=["bash"], timeout=300)):
            with pytest.raises(RuntimeError, match="timed out after 300s"):
                tools._run_script("fetch.sh", ["B08N5WRWNW"])

    def test_runs_from_repo_root(self):
        """fetch.sh expects to find config files relative to its own directory.
        We must invoke it with cwd=REPO_ROOT, not whatever cwd the MCP client
        is running from."""
        with patch("subprocess.run", return_value=_fake_completed()) as m:
            tools._run_script("fetch.sh", [])
        assert m.call_args.kwargs["cwd"] == str(tools.REPO_ROOT)

    def test_extra_env_merged(self):
        with patch("subprocess.run", return_value=_fake_completed()) as m:
            tools._run_script("fetch.sh", [], env_extra={"FOO": "bar"})
        passed_env = m.call_args.kwargs["env"]
        assert passed_env["FOO"] == "bar"
        # Shouldn't have nuked the rest of os.environ
        assert "PATH" in passed_env


# ── _parse_analyze_markdown ─────────────────────────────────────────────

class TestParseAnalyzeMarkdown:
    def setup_method(self):
        self.parsed = tools._parse_analyze_markdown("B0FAKE1234", "US", SAMPLE_REPORT)

    def test_sentiment_parsed(self):
        assert self.parsed["sentiment"] == {
            "positive": 62, "neutral": 18, "negative": 20
        }

    def test_pain_points_grouped(self):
        pp = self.parsed["pain_points"]
        assert len(pp) == 3
        assert pp[0]["en"] == "Charging port loose after 2 weeks"
        assert pp[0]["count"] == "14"
        assert pp[2]["zh"] == "说明书翻译差"

    def test_selling_points_grouped(self):
        sp = self.parsed["selling_points"]
        assert len(sp) == 3
        assert sp[0]["en"].startswith("Battery lasts")

    def test_tips_grouped(self):
        tips = self.parsed["tips"]
        assert len(tips) == 2
        assert "8-hour battery" in tips[0]["en"]

    def test_summaries(self):
        assert "well-liked product" in self.parsed["summary_en"]
        assert "电池" in self.parsed["summary_zh"]

    def test_markdown_preserved(self):
        assert self.parsed["report_markdown"] == SAMPLE_REPORT

    def test_handles_missing_fields_gracefully(self):
        """If analyze.sh emits a partial report (e.g. LLM truncation),
        the parser should return the markdown verbatim plus whatever fields
        it could extract — never throw."""
        partial = "PAIN_POINT_1_EN: Only this\nSUMMARY_EN: tiny"
        out = tools._parse_analyze_markdown("B08N5WRWNW", "US", partial)
        assert out["sentiment"] is None  # missing keys
        assert out["pain_points"] == [{"en": "Only this"}]
        assert out["summary_en"] == "tiny"

    def test_sentiment_non_numeric_falls_back_to_none(self):
        """If the LLM emits 'SENTIMENT_POSITIVE: high' instead of an int."""
        broken = (
            "SENTIMENT_POSITIVE: high\n"
            "SENTIMENT_NEUTRAL: 10\n"
            "SENTIMENT_NEGATIVE: 5\n"
        )
        out = tools._parse_analyze_markdown("B08N5WRWNW", "US", broken)
        assert out["sentiment"] is None


# ── fetch_reviews ───────────────────────────────────────────────────────

class TestFetchReviews:
    def test_writes_output_to_temp_path_and_reads_back(self, tmp_path, monkeypatch):
        """fetch_reviews creates a temp path, passes it as --output, then
        reads the JSON the script wrote."""
        captured_args: list[str] = []

        def fake_run(cmd, **kwargs):
            # cmd = ["bash", ".../fetch.sh", asin, "--limit", ..., "--output", path]
            out_idx = cmd.index("--output") + 1
            out_path = cmd[out_idx]
            captured_args.extend(cmd)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(SAMPLE_FETCH, f)
            return _fake_completed()

        with patch("subprocess.run", side_effect=fake_run):
            result = tools.fetch_reviews("B0FAKE1234", market="US", limit=3)

        assert result["meta"]["asin"] == "B0FAKE1234"
        assert len(result["reviews"]) == 3
        # Args were passed through correctly
        assert "--limit" in captured_args
        assert "3" in captured_args
        assert "--market" in captured_args
        assert "US" in captured_args

    def test_temp_file_cleaned_up_on_success(self, monkeypatch):
        seen_paths: list[str] = []

        def fake_run(cmd, **kwargs):
            out_path = cmd[cmd.index("--output") + 1]
            seen_paths.append(out_path)
            with open(out_path, "w") as f:
                json.dump(SAMPLE_FETCH, f)
            return _fake_completed()

        with patch("subprocess.run", side_effect=fake_run):
            tools.fetch_reviews("B0FAKE1234")

        assert not Path(seen_paths[0]).exists()

    def test_temp_file_cleaned_up_on_failure(self):
        """A subprocess error in fetch.sh must not leak the temp file."""
        seen: list[str] = []

        def fake_run(cmd, **kwargs):
            out_path = cmd[cmd.index("--output") + 1]
            seen.append(out_path)
            return _fake_completed(stderr="api key missing", returncode=1)

        with patch("subprocess.run", side_effect=fake_run):
            with pytest.raises(RuntimeError, match="fetch.sh failed"):
                tools.fetch_reviews("B0FAKE1234")

        # finally: cleanup ran even though we raised
        assert seen and not Path(seen[0]).exists()

    def test_rejects_bad_limit(self):
        with pytest.raises(ValueError, match="limit must be 1-1000"):
            tools.fetch_reviews("B0FAKE1234", limit=0)
        with pytest.raises(ValueError, match="limit must be 1-1000"):
            tools.fetch_reviews("B0FAKE1234", limit=5000)

    def test_rejects_bad_asin_before_subprocess(self):
        """ASIN validation must fail fast — don't spawn fetch.sh just to have
        it error."""
        with patch("subprocess.run") as m:
            with pytest.raises(ValueError, match="invalid ASIN"):
                tools.fetch_reviews("not-an-asin")
        m.assert_not_called()


# ── analyze_reviews ─────────────────────────────────────────────────────

class TestAnalyzeReviews:
    def test_accepts_wrapped_input(self):
        with patch("subprocess.run", return_value=_fake_completed(stdout=SAMPLE_REPORT)):
            out = tools.analyze_reviews(SAMPLE_FETCH, "B0FAKE1234")
        assert out["asin"] == "B0FAKE1234"
        assert out["sentiment"]["positive"] == 62
        assert len(out["pain_points"]) == 3

    def test_accepts_bare_list(self):
        """When the caller passes a raw list of reviews (no meta wrapper),
        we should still work."""
        bare = SAMPLE_FETCH["reviews"]
        with patch("subprocess.run", return_value=_fake_completed(stdout=SAMPLE_REPORT)):
            out = tools.analyze_reviews(bare, "B0FAKE1234")
        assert out["asin"] == "B0FAKE1234"

    def test_default_market_when_missing(self):
        """If the input has no meta.market, we default to US in the output."""
        bare = {"reviews": SAMPLE_FETCH["reviews"]}
        with patch("subprocess.run", return_value=_fake_completed(stdout=SAMPLE_REPORT)):
            out = tools.analyze_reviews(bare, "B0FAKE1234")
        assert out["market"] == "US"

    def test_preserves_market_from_meta(self):
        wrapped = {"reviews": SAMPLE_FETCH["reviews"], "meta": {"market": "GB"}}
        with patch("subprocess.run", return_value=_fake_completed(stdout=SAMPLE_REPORT)):
            out = tools.analyze_reviews(wrapped, "B0FAKE1234")
        assert out["market"] == "GB"

    def test_temp_file_cleaned_up(self):
        seen: list[str] = []

        def fake_run(cmd, **kwargs):
            # cmd = ["bash", ".../analyze.sh", reviews_path, asin]
            seen.append(cmd[2])
            return _fake_completed(stdout=SAMPLE_REPORT)

        with patch("subprocess.run", side_effect=fake_run):
            tools.analyze_reviews(SAMPLE_FETCH, "B0FAKE1234")

        assert seen and not Path(seen[0]).exists()


# ── voc_full ────────────────────────────────────────────────────────────

class TestVocFull:
    def test_runs_voc_sh_and_parses(self):
        with patch("subprocess.run", return_value=_fake_completed(stdout=SAMPLE_REPORT)) as m:
            out = tools.voc_full("B0FAKE1234", market="amazon.co.uk", limit=50)
        # Confirm we called voc.sh, not fetch.sh
        called_cmd = m.call_args.args[0]
        assert called_cmd[1].endswith("voc.sh")
        assert "amazon.co.uk" in called_cmd
        assert "50" in called_cmd
        # Parsed structure intact
        assert out["sentiment"]["positive"] == 62

    def test_rejects_bad_limit(self):
        with pytest.raises(ValueError, match="limit must be 1-1000"):
            tools.voc_full("B0FAKE1234", limit=10_000)


# ── extract_listing_improvements ────────────────────────────────────────

def _make_improvements() -> ListingImprovements:
    return ListingImprovements(
        title_suggestion="8-Hour Battery Pro Earbuds — Premium Build, Tested Charging Port",
        title_reasoning="Leads with the #1 selling point (battery), signals fix to #1 pain (port).",
        bullet_suggestions=[
            {"text": "8+ hours of battery on a single charge — verified by customer reviews",
             "addresses": "Battery lasts 8+ hours on a single charge"},
            {"text": "Stress-tested USB-C port engineered for 5,000+ insertions",
             "addresses": "Charging port loose after 2 weeks"},
            {"text": "Premium build quality customers describe as 'doesn't look cheap'",
             "addresses": "Build quality feels premium"},
            {"text": "Sleek modern design in Black or White",
             "addresses": "Stylish design that doesn't look cheap"},
            {"text": "Accessories arrive in a magnetic case — nothing rolls out in the box",
             "addresses": "Small accessories easily lost from packaging"},
        ],
        description_paragraph="Built for 8 hours of nonstop listening...",
        keyword_opportunities=["long battery earbuds", "premium feel", "stylish wireless"],
        warnings=["Manual translation quality is a real product issue, not a copy fix"],
    )


class TestExtractListingImprovements:
    def test_full_pipeline_with_mocked_claude(self):
        """voc.sh runs (subprocess.run mocked), then a fake Anthropic client
        returns a parsed ListingImprovements object. We verify the final
        return shape."""
        fake_client = MagicMock()
        fake_response = MagicMock()
        fake_response.parsed_output = _make_improvements()
        fake_response.stop_reason = "end_turn"
        fake_client.messages.parse.return_value = fake_response

        with patch("subprocess.run", return_value=_fake_completed(stdout=SAMPLE_REPORT)):
            out = tools.extract_listing_improvements(
                "B0FAKE1234", _client=fake_client
            )

        assert out["asin"] == "B0FAKE1234"
        assert "8-Hour Battery" in out["improvements"]["title_suggestion"]
        assert len(out["improvements"]["bullet_suggestions"]) == 5
        # Source report rolled in for traceability
        assert out["source_report"]["sentiment"]["positive"] == 62

    def test_claude_called_with_correct_model_and_features(self):
        """Lock down the model + adaptive thinking + caching contract.
        If someone downgrades the model or drops the cache_control, this
        catches it."""
        fake_client = MagicMock()
        fake_client.messages.parse.return_value = MagicMock(
            parsed_output=_make_improvements(), stop_reason="end_turn"
        )

        with patch("subprocess.run", return_value=_fake_completed(stdout=SAMPLE_REPORT)):
            tools.extract_listing_improvements("B0FAKE1234", _client=fake_client)

        call_kwargs = fake_client.messages.parse.call_args.kwargs
        assert call_kwargs["model"] == "claude-opus-4-7"
        assert call_kwargs["thinking"] == {"type": "adaptive"}
        assert call_kwargs["output_format"] is ListingImprovements
        # Cache control on the system rubric — required for cross-call cache hits
        system_blocks = call_kwargs["system"]
        assert system_blocks[0]["cache_control"] == {"type": "ephemeral"}

    def test_refusal_raises(self):
        """If Claude refuses or fails to parse, surface a clean error rather
        than returning None silently."""
        fake_client = MagicMock()
        fake_client.messages.parse.return_value = MagicMock(
            parsed_output=None, stop_reason="refusal"
        )

        with patch("subprocess.run", return_value=_fake_completed(stdout=SAMPLE_REPORT)):
            with pytest.raises(RuntimeError, match="refusal or unparseable"):
                tools.extract_listing_improvements("B0FAKE1234", _client=fake_client)

    def test_does_not_inject_per_request_data_into_system(self):
        """System prompt must be frozen — no ASIN, no timestamp, no user ID.
        Any byte change breaks prompt-cache reuse across calls."""
        fake_client = MagicMock()
        fake_client.messages.parse.return_value = MagicMock(
            parsed_output=_make_improvements(), stop_reason="end_turn"
        )

        with patch("subprocess.run", return_value=_fake_completed(stdout=SAMPLE_REPORT)):
            tools.extract_listing_improvements("B0FAKE1234", _client=fake_client)
            tools.extract_listing_improvements("B07OTHER12", _client=fake_client)

        first_system = fake_client.messages.parse.call_args_list[0].kwargs["system"]
        second_system = fake_client.messages.parse.call_args_list[1].kwargs["system"]
        assert first_system == second_system, (
            "System prompt drifted between calls — prompt cache will miss."
        )
