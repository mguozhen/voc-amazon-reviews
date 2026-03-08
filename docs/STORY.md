# 我用 AI Agent 30分钟造了一个亚马逊评论分析工具，并发布到了全球 Skill 市场

> 从想法到上线，全程用 Claude Code + OpenClaw 完成，零人工编码

---

## 背景：一个卖家的真实痛点

做亚马逊的都知道，看评论是每天必做的事。
但手动翻几百条评论，归纳痛点、找卖点、写 Listing 优化建议——

**这件事又重要，又枯燥，又耗时。**

市面上有 Helium 10、Jungle Scout，但它们：
- 贵（$50–$250/月）
- 做的是词频统计，不是真正的语义理解
- 不在你的工作流里，要切换窗口

我想要一个**直接在 AI Agent 里跑**的工具。输入 ASIN，30 秒出报告。

---

## 第一步：组建 AI 团队

我没有直接写代码。我先让 Claude Code 帮我创建了 4 个"团队 Agent"：

```
产品总控  →  负责需求定义、功能优先级、产品路线图
开发总控  →  负责技术选型、架构设计、代码实现
运营总控  →  负责用户场景、增长策略、转化设计
市场总控  →  负责定位、GTM、竞品分析
```

每个 Agent 是一个 `.md` 文件，定义了角色、职责、思维框架。

![GitHub repo](https://raw.githubusercontent.com/mguozhen/voc-amazon-reviews/main/docs/screenshots/github-repo.png)

这不是噱头。接下来的每个决策，都是通过"召唤"对应 Agent 来推进的。

---

## 第二步：4个 Agent 开会，拍板关键决策

产品总控定义了 MVP 范围。
开发总控评估了技术方案。
运营总控补充了用户场景。
市场总控给出了差异化定位。

**4个决策被快速拍板：**

| 决策 | 结论 |
|---|---|
| 数据来源 | 自建爬虫（不用付费 API）|
| 目标平台 | OpenClaw（面向 AI Agent 用户）|
| MVP 范围 | 单 ASIN 分析（不做竞品对比）|
| 报告语言 | 中英双语 |

![ClawHub skill page](https://raw.githubusercontent.com/mguozhen/voc-amazon-reviews/main/docs/screenshots/clawhub.png)

---

## 第三步：30分钟，Skill 从 0 到可运行

整个 Skill 由 4 个文件组成：

```
voc-amazon-reviews/
├── SKILL.md      ← AI 读这个，知道怎么调用这个 skill
├── voc.sh        ← 主入口，接收 ASIN 参数
├── scraper.sh    ← 用 browse CLI 抓取亚马逊评论
└── analyze.sh    ← 调用 OpenClaw 模型做 VOC 分析
```

**核心技术选择：**

爬虫用的是 `browse CLI`（OpenClaw 生态里的浏览器自动化工具），而不是 curl——因为亚马逊有反爬，真实浏览器才能拿到数据。

分析用的是 **OpenClaw 当前配置的默认模型**（我这里是 `gpt-5.2`），不需要单独配 API Key。

![VOC Report Output](https://raw.githubusercontent.com/mguozhen/voc-amazon-reviews/main/docs/screenshots/voc-report.png)

---

## 第四步：真实测试 — ASIN B0F6VWT6SP

我用的是亚马逊上的 **Blink Video Doorbell + Outdoor 4 XR**（4.6星，324条评论）来测试。

**遇到的问题和解法：**

| 问题 | 解法 |
|---|---|
| curl 直接被反爬拦截 | 改用 browse CLI 打开真实浏览器 |
| 评论页需要登录 | 改抓商品页的 Top Reviews（无需登录）|
| Claude API 余额不足 | 改成调用 OpenClaw 本地模型 |
| Claude Code 不能嵌套调用 | 改用 `openclaw agent --local` |

每个问题遇到 → AI 给方案 → 立刻改 → 继续跑。

**最终抓到 7 条评论，跑出了完整报告：**

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
1. Live view extremely laggy（核心差评原因）
2. Motion detection unreliable
3. Battery life unproven

🟢 Top Selling Points
1. Incredibly easy to install（6/7条均提及）
2. No subscription + local SD storage
3. XR extended range up to 400ft

💡 Listing Optimization
1. 在标题加电池容量，管理续航预期
2. 第一条 bullet 突出"无订阅费"，对标 Ring/Nest
3. 用"up to 400ft"量化 XR 优势，加农场/大院场景图
```

---

## 第五步：发布到全球 Skill 市场

**GitHub：**
```bash
git init && git push origin main
```

**ClawHub（AI Agent 的 App Store）：**
```bash
npm install -g clawhub
clawhub login
clawhub publish ./voc-amazon-reviews --slug voc-amazon-reviews --version 1.0.0
```

![ClawHub Published](https://raw.githubusercontent.com/mguozhen/voc-amazon-reviews/main/docs/screenshots/clawhub.png)

发布完成后，任何人都可以一行命令安装：

```bash
clawhub install voc-amazon-reviews
```

---

## 第六步：产品文档一步到位

产品总控输出了 **Roadmap**：
- Phase 1：8条免费评论 → 引导至官网付费解锁全量
- Phase 2：转化优化（ASIN 带参跳转、UTM 追踪）
- Phase 3：付费用户直连 API，多 ASIN 批量分析

市场总控输出了 **GTM 策略**：
- 种子期：ClawHub + GitHub + Reddit
- 扩散期：跨境论坛 + 微信群 + KOL
- 转化期：Case Study + 报告内 CTA + 限时折扣

![Roadmap doc](https://raw.githubusercontent.com/mguozhen/voc-amazon-reviews/main/docs/screenshots/roadmap.png)

---

## 整个过程的时间线

```
00:00  提出想法：为亚马逊卖家做 VOC 分析 Skill
05:00  4个团队 Agent 创建完毕
15:00  4个关键决策拍板
30:00  SKILL.md + voc.sh + scraper.sh + analyze.sh 写完
45:00  真实 ASIN 测试，踩坑+修复
60:00  报告跑通，输出质量符合预期
70:00  推送 GitHub，发布 ClawHub
80:00  Roadmap + GTM 文档落地
```

**全程：约 80 分钟。零人工编码。**

---

## 我学到的

**1. 先组团队，再干活**
4个 Agent 的设定看起来是"过度设计"，但它让每个决策都有明确的视角。产品想的和开发想的不一样——让 AI 扮演不同角色，就是在模拟这种张力。

**2. 遇到墙就绕，不要硬撞**
亚马逊反爬 → 换浏览器。API 余额不足 → 换模型。Claude 嵌套限制 → 用 openclaw agent。每次遇到障碍，AI 都能给出备选方案。

**3. 文档和代码同等重要**
Roadmap、GTM、README，这些文档让工具"活"起来。没有它们，代码只是代码。

---

## 现在就可以用

```bash
# 安装
clawhub install voc-amazon-reviews

# 使用
bash skills/voc-amazon-reviews/voc.sh B0F6VWT6SP
```

或者直接在 OpenClaw 里说：
> "Analyze the reviews for ASIN B0F6VWT6SP"

GitHub：https://github.com/mguozhen/voc-amazon-reviews
ClawHub：clawhub install voc-amazon-reviews

---

*用 Claude Code + OpenClaw 构建 | Build with AI, ship with AI*
