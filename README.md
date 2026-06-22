# BrainKnowledge 大脑知识库

关于元认知、认知科学、大脑工作原理的系统性笔记。

每个文件对应一个知识点，包含详细解释与参考来源。

## 目录

完整的分类索引见 **[[index]]**（按 7 大主题归类全部笔记，是检索入口）。

## 工具技能（Skills）

本仓库在 `.claude/skills/` 下安装了 5 个 [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)（Obsidian 官方出品），为本知识库提供 Obsidian 原生能力。下面结合本库笔记说明每个 skill 的典型用法。

### 1. `obsidian-markdown` — Obsidian 风格 Markdown ✅ 开箱即用

给笔记加上 wikilink、callout、properties 等 Obsidian 专有语法。

- 给 `心流状态.md` 加 callout 高亮：`> [!note] 定义` 放一句话定义，`> [!warning] 易混淆` 区分它与 `爽片沉溺与奖赏回路`。
- 把「多巴胺/成瘾」主题的笔记用 `[[双向链接]]` 串起来：`游戏成瘾_被操控感与逃避现实` ←→ `竞技网游vs探索游戏的多巴胺成瘾机制` ←→ `心流状态`。
- 给所有笔记补 frontmatter properties（如 `神经递质: [多巴胺]`、`脑区: [前额叶]`、`tags`），为下面的 Bases 视图打基础。

### 2. `obsidian-bases` — `.base` 数据库视图 ✅ 开箱即用

基于 properties 把一堆 `.md` 渲染成可筛选的动态表格 / 卡片视图。

- 建「按神经递质分类.base」：自动把含「多巴胺」「血清素」「皮质醇」的笔记分组成表（如归拢 `社会比较焦虑与血清素`、`最健康睡眠方式与皮质醇节律`）。
- 建「最近更新.base」cards 视图，按更新时间倒序，替代手动维护本目录。
- 建「待补充.base」：筛选出缺少「参考来源」章节的笔记，方便查漏补缺。

### 3. `json-canvas` — `.canvas` 画布 / 关系图 ✅ 开箱即用

把知识点连成可视化白板，节点嵌入笔记、连线表达因果关联。

- 「多巴胺与成瘾」关系图：`不确定性与多巴胺_预测误差` →（奖赏回路）→ `游戏成瘾` / `爽片沉溺` / `心流状态`。
- 「睡眠—晨起」时间线：`最健康睡眠方式与皮质醇节律` → `梦多与REM反弹现象` → `早晨起床后情绪失控`。
- 「焦虑机制」因果图：`为什么大脑会默认先想坏结果` → `焦虑未来与负面偏差` → `焦虑逃避循环与身体应激反应`。

### 4. `defuddle` — 网页转干净 Markdown ⚙️ 依赖 Defuddle CLI（已安装）

抓取网页正文并剥离导航/广告，转成 markdown，比 WebFetch 省 token。

- 给一篇讲多巴胺预测误差的论文/科普网页链接，`defuddle parse <url> --md` 抓成干净正文，作为新笔记的「参考来源」素材。
- 整理 `睡眠机制` 时，把 PubMed 或科普文章正文提取出来直接入库，省去手动复制清理。
- 读 Nature / Scientific American 文章时先转 md，再按本库笔记格式提炼成知识点。

### 5. `obsidian-cli` — 命令行操控 Obsidian ⚙️ 依赖 Obsidian CLI（已安装，需 Obsidian 运行中）

直接对运行中的 Obsidian 读 / 建 / 搜笔记、查链接。

- `obsidian search query="多巴胺"` 一键找出所有相关笔记。
- `obsidian create name="新知识点" content="..."` 按格式快速建笔记。
- `obsidian backlinks file="心流状态"` 查看哪些笔记反向引用了它。

---

> 由 Claude Code `/元认知` 命令自动生成并维护
