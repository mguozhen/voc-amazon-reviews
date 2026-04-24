# I Built an Amazon Review Analysis Tool in 30 Minutes with AI Agents, Then Published It to the Global Skill Marketplace

> From idea to launch — built entirely with Claude Code + OpenClaw, zero manual coding

---

## Background: A Real Pain Point for Sellers

Anyone who sells on Amazon knows: reading reviews is something you do every single day.
But manually sifting through hundreds of reviews to identify pain points, surface selling points, and write Listing optimization suggestions —

**It's important. It's tedious. It's time-consuming.**

Tools like Helium 10 and Jungle Scout exist, but they:
- Are expensive ($50–$250/month)
- Do keyword counting, not real semantic understanding
- Live outside your workflow, forcing constant context-switching

I wanted a tool that runs **directly inside an AI Agent**. Input an ASIN, get a report in 30 seconds.

---

## Step 1: Assemble the AI Team

I didn't start by writing code. I had Claude Code create 4 "team Agents" first:

```
Product Lead  →  requirements, feature priorities, product roadmap
Dev Lead      →  tech stack, architecture, code implementation
Growth Lead   →  user scenarios, growth strategy, conversion design
Marketing Lead →  positioning, GTM, competitor analysis
```

Each Agent is a `.md` file defining its role, responsibilities, and thinking framework.

![GitHub repo](https://raw.githubusercontent.com/mguozhen/voc-amazon-reviews/main/docs/screenshots/github-repo.png)

This wasn't just for show. Every subsequent decision was made by "summoning" the appropriate Agent.

---

## Step 2: 4 Agents in a Meeting — Making Key Decisions

The Product Lead defined the MVP scope.
The Dev Lead evaluated the technical approach.
The Growth Lead added user scenarios.
The Marketing Lead provided differentiated positioning.

**4 decisions were locked in quickly:**

| Decision | Outcome |
|---|---|
| Data source | Custom scraper (no paid API) |
| Target platform | OpenClaw (AI Agent user base) |
| MVP scope | Single ASIN analysis (no competitor comparison) |
| Report language | English + Chinese bilingual |

![ClawHub skill page](https://raw.githubusercontent.com/mguozhen/voc-amazon-reviews/main/docs/screenshots/clawhub.png)

---

## Step 3: 30 Minutes — Skill from Zero to Running

The entire Skill consists of 4 files:

```
voc-amazon-reviews/
├── SKILL.md      ← AI reads this to know how to invoke the skill
├── voc.sh        ← main entry point, takes ASIN argument
├── scraper.sh    ← uses browse CLI to fetch Amazon reviews
└── analyze.sh    ← calls OpenClaw model for VOC analysis
```

**Core technical choices:**

The scraper used `browse CLI` (the browser automation tool in the OpenClaw ecosystem), not curl — because Amazon has anti-scraping measures, and only a real browser can get the data.

The analysis used the **default model configured in OpenClaw** (mine was `gpt-5.2`), so no separate API key needed.

![VOC Report Output](https://raw.githubusercontent.com/mguozhen/voc-amazon-reviews/main/docs/screenshots/voc-report.png)

---

## Step 4: Real Test — ASIN B0F6VWT6SP

I used the **Blink Video Doorbell + Outdoor 4 XR** on Amazon (4.6 stars, 324 reviews) to test.

**Problems encountered and solutions:**

| Problem | Solution |
|---|---|
| curl blocked by anti-scraping | Switched to browse CLI for a real browser |
| Review page requires login | Switched to scraping Top Reviews on product page (no login needed) |
| Claude API credits depleted | Switched to calling OpenClaw local model |
| Claude Code can't nest calls | Used `openclaw agent --local` instead |

Each problem encountered → AI provides solution → fix immediately → continue running.

**Result: 7 reviews captured, full report generated:**

![VOC Report](https://raw.githubusercontent.com/mguozhen/voc-amazon-reviews/main/docs/screenshots/voc-report.png)

```
╔══════════════════════════════════════════════════════════════╗
║                  VOC AI Analysis Report                     ║
║  ASIN: B0F6VWT6SP  |  analyzed: 7 reviews                  ║
╚══════════════════════════════════════════════════════════════╝

📊 Sentiment Distribution
  Positive  █████████████████░░░  86%
  Negative  ███░░░░░░░░░░░░░░░░░  14%

🔴 Top Pain Points
1. Live view extremely laggy (core complaint)
2. Motion detection unreliable
3. Battery life unproven

🟢 Top Selling Points
1. Incredibly easy to install (6/7 reviews mention this)
2. No subscription + local SD storage
3. XR extended range up to 400ft

💡 Listing Optimization
1. Add battery capacity to title to manage range expectations
2. Lead first bullet with "no subscription fee" — differentiate from Ring/Nest
3. Quantify the XR advantage with "up to 400ft" and add farm/large yard scenario images
```

---

## Step 5: Publish to the Global Skill Marketplace

**GitHub:**
```bash
git init && git push origin main
```

**ClawHub (the App Store for AI Agents):**
```bash
npm install -g clawhub
clawhub login
clawhub publish ./voc-amazon-reviews --slug voc-amazon-reviews --version 1.0.0
```

![ClawHub Published](https://raw.githubusercontent.com/mguozhen/voc-amazon-reviews/main/docs/screenshots/clawhub.png)

Once published, anyone can install it with one command:

```bash
clawhub install voc-amazon-reviews
```

---

## Step 6: Product Documentation in One Pass

The Product Lead produced the **Roadmap**:
- Phase 1: 8 free reviews → guide to the website to unlock full analysis with a paid plan
- Phase 2: Conversion optimization (ASIN pre-fill redirect, UTM tracking)
- Phase 3: Paid users connect API directly, batch multi-ASIN analysis

The Marketing Lead produced the **GTM strategy**:
- Seed phase: ClawHub + GitHub + Reddit
- Amplification phase: cross-border forums + WeChat groups + KOLs
- Conversion phase: case studies + in-report CTA + limited-time offers

![Roadmap doc](https://raw.githubusercontent.com/mguozhen/voc-amazon-reviews/main/docs/screenshots/roadmap.png)

---

## Full Timeline

```
00:00  Idea: build a VOC analysis Skill for Amazon sellers
05:00  4 team Agents created
15:00  4 key decisions made
30:00  SKILL.md + voc.sh + scraper.sh + analyze.sh complete
45:00  Real ASIN testing, hit issues, made fixes
60:00  Report running cleanly, output quality meets expectations
70:00  Pushed to GitHub, published to ClawHub
80:00  Roadmap + GTM docs finalized
```

**Total: ~80 minutes. Zero manual coding.**

---

## What I Learned

**1. Form the team first, then do the work**
The 4-Agent setup looks like "over-engineering," but it forces every decision to have a clear perspective. What Product wants and what Dev wants are different — having AI play different roles simulates that tension.

**2. Hit a wall? Go around it, don't force through**
Amazon anti-scraping → switch to real browser. API credits depleted → switch models. Claude nesting limit → use openclaw agent. Every time you hit a blocker, AI can offer alternatives.

**3. Documentation matters as much as code**
Roadmap, GTM, README — these documents make the tool *alive*. Without them, code is just code.

---

## Try It Now

```bash
# Install
clawhub install voc-amazon-reviews

# Use
bash skills/voc-amazon-reviews/voc.sh B0F6VWT6SP
```

Or just say in OpenClaw:
> "Analyze the reviews for ASIN B0F6VWT6SP"

GitHub: https://github.com/mguozhen/voc-amazon-reviews
ClawHub: clawhub install voc-amazon-reviews

---

*Built with Claude Code + OpenClaw | Build with AI, ship with AI*
