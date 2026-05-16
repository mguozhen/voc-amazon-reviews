# 多平台分发文案 — 2026-05-15

源稿：`docs/blog/2026-05-15-mcp-launch.md`（约 1800 字中文长文，定位"数据层是 moat"）
GitHub：`https://github.com/mguozhen/voc-amazon-reviews`
Hero image：`docs/blog/assets/hero-data-moat.jpg`

每个平台一份独立 adapt，**不要原文直搬**（每个平台算法和读者口味都不一样）。

---

## 1. X / Twitter 主帖（thread，英文，10 条）

**1/10**
Amazon seller tools all chase "better AI."

The dirty secret: the AI is fine. **The data underneath is broken.**

We open-sourced the fix. 👇

🧵

**2/10**
What's broken about most seller-tool data:

→ Scrapers crash when Amazon ships a CSS change
→ "Free" tier caps you at 10–50 reviews
→ Daily snapshots, sometimes cached for days
→ verified_purchase / helpful_votes / vine_voice silently dropped
→ Multi-market = afterthought (most are US-only)

**3/10**
We built voc-amazon-reviews around the opposite premise:

The review data layer should be **boring, reliable, complete, and AI-native.**

Everything else — sentiment analysis, pain points, listing copy gen, the MCP server — is downstream of that.

**4/10**
Here's what "stable + complete" actually means:

✓ Paid OpenAPI (Shulex VOC) — not scraping
✓ 10 marketplaces: US/CA/MX/GB/DE/FR/IT/ES/JP/AU
✓ Up to 1,000 reviews per ASIN per call
✓ Full schema: verified, helpful, vine, variant, dates
✓ Live, not cached
✓ Non-English markets native (JP/DE/FR/IT/ES)

**5/10**
The new shipped piece: a Model Context Protocol (MCP) server.

4 tools, all powered by the same data layer:

• fetch_reviews
• analyze_reviews
• voc_full
• extract_listing_improvements ★

Plugs into Claude Desktop / Code / Cursor / Windsurf in one config block.

**6/10**
`extract_listing_improvements` is where the data quality pays off.

Input: an ASIN.
Output: proposed title, 5 bullets, description, missing keywords — **each suggestion citing the specific review evidence it addresses.**

No invented benefits. No SEO black magic.

**7/10**
Also a `warnings` field. The model proactively flags issues that **can't be fixed in listing copy** — like "Manual translation quality is a real product problem; better copy won't fix it; you need a translator pass."

Better copy on a broken product = more returns, not more sales.

**8/10**
Compare with Data Dive's MCP (their MCP is good, but limited):

| | Data Dive | This |
|---|---|---|
| Open source | ❌ | ✅ |
| BYO API key | ❌ | ✅ |
| Markets | US-first | 10 native |
| Listing copy | ❌ | ✅ w/ citations |
| Product-issue warnings | ❌ | ✅ |
| Self-hosted | ❌ | ✅ |

**9/10**
Stack:

• Python MCP SDK (FastMCP)
• Thin subprocess wrapper over the existing shell skill
• Claude Opus 4.7 for extract_listing_improvements, with prompt caching on the rubric
• 36 fully-offline pytest unit tests
• MIT license

**10/10**
Open source. BYO API key. No vendor in your data path.

→ github.com/mguozhen/voc-amazon-reviews

If you build seller tooling — fork it. If you're a seller — use it. If you have a brutal review-analysis need we haven't covered, tell me; next tool is yours.

---

## 2. 小红书 帖文（中文，~600 字，配 hero 图 + 截图）

**标题**：亚马逊卖家工具99%都做错了 我搞了个开源版本

**正文**：

最近发现一件事 ——

亚马逊卖家用的那些工具，每个都说自己 AI 化了。Helium 10 有，Jungle Scout 有，Data Dive 刚出了 MCP。

**但你打开任何一个 demo 看 10 秒就知道不对劲**：同一个 ASIN，A 工具说核心抗议是"充电问题"，B 工具说是"按键松动"。为什么俩工具读同一个 ASIN 结论不一样？

因为他们抓的不是同一批评论 ——一个抓了 20 条快照、另一个 50 条还是上周缓存的。**AI 不是问题，数据才是。**

🔍 主流工具的数据层都长这样：

❌ 爬虫一改 HTML 全炸
❌ 免费档 10-50 条封顶  
❌ 缓存几天没人更
❌ verified purchase / helpful votes 字段经常丢
❌ 95% 工具只支持美区

所以我做了个开源项目：**voc-amazon-reviews**

✅ 付费 OpenAPI（Shulex VOC），不是爬虫
✅ 10 个市场全 native：US / CA / MX / GB / DE / FR / IT / ES / JP / AU  
✅ 单 ASIN 最多抓 1000 条评论
✅ 完整字段：评分 / 正文 / verified / helpful / Vine / 变体 / 日期
✅ 实时拉取，不是快照
✅ 日德法意西原文捕获，AI 翻译给你看

然后顺手接到了 Claude / Cursor / Windsurf —— 4 个 MCP 工具一键调用。

💡 最骚的工具叫 `extract_listing_improvements`：喂一个 ASIN，**Claude 直接给你写出标题 + 5 条 bullets + 描述 + 漏抓的关键词**，每条建议都附上是基于评论里哪句具体话写的。

而且会主动警告："这些问题改文案解决不了，是产品本身的问题"——这个 honesty 在卖家工具圈是稀缺的。

🔗 GitHub：mguozhen/voc-amazon-reviews（开源、免费、BYO API key）

跨境电商朋友自取。如果你有自己最痛的"评论分析"需求，评论区告诉我，下一个工具按你的痛点来。

#亚马逊卖家 #跨境电商 #amazon #AI工具 #开源

---

## 3. Reddit — r/FulfillmentByAmazon（英文长文，I-built-this 风格）

**标题**：I open-sourced an Amazon review analysis MCP server (works with Claude / Cursor / Windsurf) — focused on data quality, not AI gimmicks

**正文**：

Long-time lurker, sometimes-poster. I run a couple of FBA stores and a small dev consultancy. Built this because I was tired of cross-referencing 4 different "AI review tools" that all gave conflicting answers about the same ASIN.

**The real problem with AI review tools isn't the AI.** It's that the data underneath is bad.

I checked. Same ASIN, 3 popular tools:

- Tool A: "top pain point is charging port issues"
- Tool B: "top pain point is button stickiness"  
- Tool C: "top pain point is battery life"

Why? Because they're not reading the same reviews:
- Tool A scraped 18 reviews from 3 weeks ago
- Tool B has 35 reviews cached from a daily snapshot
- Tool C wraps an undocumented API that drops `verified_purchase` flags

Each tool has good AI analysis on top of bad data, so they're producing confidently-wrong conclusions. None tells you their data layer is the issue.

**What I did**: built voc-amazon-reviews on top of Shulex VOC OpenAPI (paid, professional, no scraping). That gets you:

- 10 marketplaces (US/CA/MX/GB/DE/FR/IT/ES/JP/AU)
- Up to 1,000 reviews per ASIN per call
- Full schema preserved (verified, helpful, vine, variant, dates)
- Live, not cached
- Non-English markets native

Open-sourced the whole thing including the MCP server that plugs it into Claude / Cursor / Windsurf.

**One tool I'm particularly happy with**: `extract_listing_improvements`. Input an ASIN, output:

- Proposed title (with reasoning)
- 5 bullet suggestions, **each one citing the specific pain point or selling point it addresses** (no invented benefits, all grounded in actual review language)
- Description paragraph
- Missing keywords (pulled from buyer language, not SEO assumptions)
- **`warnings` field** for issues that can't be fixed with copy — e.g., if reviews show a real product defect, the tool says "better copy won't fix this; you need a product fix"

That last bit is what I really wanted that no other tool does — better copy on a broken product just gets you more returns.

**Cost**: Shulex VOC has a free starter tier (~100 credits, enough for ~10 ASINs of light analysis). Anthropic API for the listing-improvements tool is ~$0.05–0.20 per call (Opus 4.7 with adaptive thinking).

**Stack**: Python, ~600 lines for the MCP server, 36 pytest unit tests (fully offline so CI works without API keys). MIT license.

GitHub: https://github.com/mguozhen/voc-amazon-reviews

Happy to take feedback. If you've got a "I read 200 reviews of this ASIN every Tuesday and I'm tired" workflow, tell me about it — that's the next tool I'd want to build.

---

## 4. Hacker News — 标题 + 首条评论 seed

**标题**（要点：技术诚实、不带营销词、勾起好奇）：

> Show HN: An MCP server for Amazon review analysis — the data is the moat

**首条 self-comment（HN 文化：作者自己发一条额外背景）**：

Author here. A bit of context that didn't fit in the README:

The interesting design problem with this project wasn't the MCP layer (FastMCP makes that ~150 lines). It was admitting that **the AI analysis layer is a commodity** in this space — every seller tool has it now — and the actual differentiation has to come from the data underneath.

For Amazon review data specifically, that means:

1. **Not scraping.** Scrapers work until Amazon ships a CSS change. For a production tool this is a flip-coin reliability bet I didn't want to make.
2. **Full schema preserved.** Most scraped tools silently drop `verified_purchase` and `helpful_votes`. Those two fields alone change which complaints are real and which are competitor sock-puppet reviews. Losing them halves the signal.
3. **Non-English markets.** Building a German VOC report from machine-translated previews vs. the actual German review text is a different product.
4. **Live, not cached.** The whole point of a "what are buyers saying right now" tool is broken if your snapshot is 3 days old.

So the project is fundamentally a thin open-source wrapper around Shulex VOC's paid OpenAPI, plus an MCP server that makes it AI-callable, plus one differentiator tool (`extract_listing_improvements`) that uses Claude Opus 4.7 with structured outputs to turn a VOC report into copyable listing edits — every suggestion citing the specific review evidence.

The MCP server is the headline because it makes the project useful inside Claude Desktop / Code / Cursor / Windsurf without anyone writing integration code. But the headline is the delivery channel, not the moat.

Repo: https://github.com/mguozhen/voc-amazon-reviews (MIT). Happy to answer questions or take PRs.

---

## 发布顺序建议

| 平台 | 时间窗口 | 节奏 | 备注 |
|---|---|---|---|
| **X/Twitter thread** | 周二 / 周三 美东上午 9-11 | 一次性发完整 10 条 | hero 图作为第 1 条配图；后面几条按需配代码截图 |
| **小红书** | 周二 / 周三 晚 8-10 | hero 图 + 1-2 张截图（README + Claude Desktop 调用截图）| 标签别超过 5 个，按"亚马逊卖家"为主 |
| **Reddit r/FulfillmentByAmazon** | 周三 / 周四 美东上午 7-9 | 单贴长文 | 不带过多链接（Reddit 不喜欢自我推广式） |
| **Hacker News** | 周二 / 周三 太平洋时间上午 7-9 | Show HN + self-comment | 一次机会，标题要重，第一小时决定生死 |

**通用守则**：
- 任何回复都用第一人称、不卖货，回答问题为主
- 评论区出现"why not just scrape?"的问题——把 README 里"AI clients table"那段贴出去
- 别同时发完——错开 24-48 小时让每个平台有自己的讨论窗口

要不要我顺带帮你跑一遍 `multi-platform-publisher` skill 自动推送？还是你自己想看着发？
