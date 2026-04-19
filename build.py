#!/usr/bin/env python3
"""
BrainKnowledge 网站构建脚本
读取所有 .md 文件 → 生成 index.html（用于 GitHub Pages 部署）
"""
import os
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent

def read_md_files():
    entries = []
    skip = {"README.md", "build.py"}
    for f in sorted(BASE_DIR.glob("*.md")):
        if f.name in skip:
            continue
        content = f.read_text(encoding="utf-8")
        # 提取标题（第一个 # 行）
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f.stem
        # 提取更新时间
        date_match = re.search(r"更新时间[：:]\s*(.+)", content)
        date = date_match.group(1).strip() if date_match else ""
        entries.append({
            "id": re.sub(r"[^\w\u4e00-\u9fff]", "_", f.stem),
            "title": title,
            "date": date,
            "content": content,
            "filename": f.stem
        })
    return entries

def build_html(entries):
    count = len(entries)
    entries_json = json.dumps(entries, ensure_ascii=False)

    sidebar_items = "\n".join(
        f'    <li><a href="#" class="nav-link" data-id="{e["id"]}" onclick="showEntry(\'{e["id"]}\');return false;">'
        f'{e["title"]}</a></li>'
        for e in entries
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BrainKnowledge — 大脑知识库</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=Noto+Serif+SC:wght@400;600&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --bg:       #0b0f18;
  --sidebar:  #101520;
  --card:     #161d2e;
  --card-bd:  rgba(255,255,255,0.06);
  --text:     #ddd6c8;
  --muted:    #7a8499;
  --gold:     #e8a74c;
  --gold-dim: rgba(232,167,76,0.12);
  --blue:     #7dd3fc;
  --green:    #86efac;
  --purple:   #c4b5fd;
  --sidebar-w: 280px;
}}

html {{ scroll-behavior: smooth; }}

body {{
  background: var(--bg);
  color: var(--text);
  font-family: 'DM Sans', 'Noto Serif SC', serif;
  min-height: 100vh;
  display: flex;
}}

/* ── SIDEBAR ── */
.sidebar {{
  width: var(--sidebar-w);
  min-height: 100vh;
  background: var(--sidebar);
  border-right: 1px solid var(--card-bd);
  position: fixed;
  top: 0; left: 0; bottom: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}

.sidebar-brand {{
  padding: 28px 24px 20px;
  border-bottom: 1px solid var(--card-bd);
}}

.brand-label {{
  font-size: 10px;
  letter-spacing: 0.2em;
  color: var(--gold);
  text-transform: uppercase;
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  margin-bottom: 6px;
}}

.brand-title {{
  font-family: 'Playfair Display', serif;
  font-size: 22px;
  font-weight: 700;
  color: #f0ece3;
  line-height: 1.2;
}}

.brand-sub {{
  font-size: 12px;
  color: var(--muted);
  margin-top: 6px;
  font-family: 'Noto Serif SC', serif;
}}

.search-wrap {{
  padding: 16px 16px 12px;
  border-bottom: 1px solid var(--card-bd);
}}

.search-input {{
  width: 100%;
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--card-bd);
  border-radius: 8px;
  color: var(--text);
  font-size: 13px;
  padding: 9px 12px;
  font-family: 'Noto Serif SC', serif;
  outline: none;
  transition: border-color 0.2s;
}}
.search-input::placeholder {{ color: var(--muted); }}
.search-input:focus {{ border-color: var(--gold); }}

.nav-count {{
  padding: 10px 18px 6px;
  font-size: 11px;
  color: var(--muted);
  font-family: 'DM Sans', sans-serif;
  letter-spacing: 0.05em;
}}

.nav-list {{
  list-style: none;
  overflow-y: auto;
  flex: 1;
  padding: 4px 0 20px;
}}

.nav-list::-webkit-scrollbar {{ width: 4px; }}
.nav-list::-webkit-scrollbar-track {{ background: transparent; }}
.nav-list::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 4px; }}

.nav-link {{
  display: block;
  padding: 10px 20px;
  font-size: 13px;
  color: var(--muted);
  text-decoration: none;
  font-family: 'Noto Serif SC', serif;
  border-left: 2px solid transparent;
  transition: all 0.18s;
  line-height: 1.4;
  cursor: pointer;
}}
.nav-link:hover, .nav-link.active {{
  color: var(--gold);
  border-left-color: var(--gold);
  background: var(--gold-dim);
}}

/* ── MAIN ── */
.main {{
  margin-left: var(--sidebar-w);
  flex: 1;
  padding: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}}

/* 欢迎页 */
.welcome {{
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 48px;
  text-align: center;
}}

.welcome-icon {{
  font-size: 56px;
  margin-bottom: 24px;
  opacity: 0.6;
}}

.welcome h1 {{
  font-family: 'Playfair Display', serif;
  font-size: 40px;
  color: #f0ece3;
  letter-spacing: -0.02em;
  margin-bottom: 12px;
}}

.welcome p {{
  color: var(--muted);
  font-size: 15px;
  font-family: 'Noto Serif SC', serif;
  line-height: 1.8;
}}

.welcome-stats {{
  display: flex;
  gap: 32px;
  margin-top: 36px;
}}

.stat {{
  text-align: center;
}}

.stat-num {{
  font-family: 'Playfair Display', serif;
  font-size: 32px;
  color: var(--gold);
}}

.stat-label {{
  font-size: 12px;
  color: var(--muted);
  font-family: 'DM Sans', sans-serif;
  margin-top: 4px;
}}

/* 文章页 */
.article-page {{
  display: none;
  flex: 1;
  flex-direction: column;
}}

.article-page.visible {{
  display: flex;
}}

.article-header {{
  padding: 40px 52px 28px;
  border-bottom: 1px solid var(--card-bd);
  background: rgba(255,255,255,0.01);
}}

.article-date {{
  font-size: 11px;
  letter-spacing: 0.15em;
  color: var(--muted);
  text-transform: uppercase;
  font-family: 'DM Sans', sans-serif;
  margin-bottom: 12px;
}}

.article-title {{
  font-family: 'Playfair Display', serif;
  font-size: 36px;
  color: #f0ece3;
  letter-spacing: -0.02em;
  line-height: 1.2;
}}

.article-body {{
  padding: 40px 52px 80px;
  flex: 1;
  overflow-y: auto;
  max-width: 820px;
}}

/* Markdown 渲染样式 */
.article-body h1 {{ display: none; }}

.article-body h2 {{
  font-family: 'Playfair Display', serif;
  font-size: 22px;
  color: var(--gold);
  margin: 36px 0 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--gold-dim);
  font-weight: 700;
}}

.article-body h2:first-of-type {{
  margin-top: 0;
}}

.article-body h3 {{
  font-size: 13px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  margin: 22px 0 10px;
}}

.article-body p {{
  font-size: 14.5px;
  line-height: 1.85;
  color: var(--text);
  margin-bottom: 14px;
  font-family: 'Noto Serif SC', serif;
}}

.article-body ul, .article-body ol {{
  padding-left: 20px;
  margin-bottom: 14px;
}}

.article-body li {{
  font-size: 14px;
  line-height: 1.8;
  color: var(--text);
  font-family: 'Noto Serif SC', serif;
  margin-bottom: 4px;
}}

.article-body strong {{
  color: #f0ece3;
  font-weight: 600;
}}

.article-body em {{
  color: var(--blue);
  font-style: italic;
}}

.article-body blockquote {{
  border-left: 3px solid var(--gold);
  padding: 10px 16px;
  margin: 16px 0;
  background: var(--gold-dim);
  border-radius: 0 8px 8px 0;
}}

.article-body blockquote p {{
  color: rgba(232,167,76,0.9);
  font-size: 13.5px;
  margin: 0;
}}

.article-body code {{
  background: rgba(255,255,255,0.06);
  border: 1px solid var(--card-bd);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 12.5px;
  color: var(--green);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}}

.article-body pre {{
  background: rgba(0,0,0,0.3);
  border: 1px solid var(--card-bd);
  border-radius: 10px;
  padding: 18px 20px;
  margin: 16px 0;
  overflow-x: auto;
}}

.article-body pre code {{
  background: none;
  border: none;
  padding: 0;
  font-size: 13px;
  color: var(--text);
  line-height: 1.7;
}}

.article-body table {{
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: 13.5px;
  font-family: 'Noto Serif SC', serif;
}}

.article-body th {{
  background: rgba(232,167,76,0.1);
  color: var(--gold);
  font-weight: 600;
  padding: 10px 14px;
  border: 1px solid rgba(232,167,76,0.2);
  text-align: left;
  font-family: 'DM Sans', sans-serif;
  font-size: 12px;
  letter-spacing: 0.05em;
}}

.article-body td {{
  padding: 9px 14px;
  border: 1px solid var(--card-bd);
  color: var(--text);
  line-height: 1.6;
}}

.article-body tr:hover td {{
  background: rgba(255,255,255,0.02);
}}

.article-body hr {{
  border: none;
  border-top: 1px solid var(--card-bd);
  margin: 28px 0;
}}

/* 来源区块特殊样式 */
.article-body ul li:has(a) {{
  color: var(--muted);
  font-size: 13px;
}}

.article-body a {{
  color: var(--blue);
  text-decoration: none;
}}
.article-body a:hover {{
  text-decoration: underline;
}}

/* 搜索无结果 */
.no-result {{
  text-align: center;
  color: var(--muted);
  padding: 40px 0;
  font-family: 'Noto Serif SC', serif;
  font-size: 13px;
  display: none;
}}

@media (max-width: 768px) {{
  .sidebar {{ display: none; }}
  .main {{ margin-left: 0; }}
  .article-header, .article-body {{ padding-left: 24px; padding-right: 24px; }}
}}
</style>
</head>
<body>

<aside class="sidebar">
  <div class="sidebar-brand">
    <div class="brand-label">Brain Knowledge</div>
    <div class="brand-title">大脑<br>知识库</div>
    <div class="brand-sub">元认知 · 认知科学 · 神经机制</div>
  </div>
  <a href="http://127.0.0.1:8765/brain-3d.html" target="_blank" style="display:block;padding:12px 24px;font-size:13px;color:var(--gold);text-decoration:none;font-family:'Noto Serif SC',serif;border-bottom:1px solid var(--card-bd);background:var(--gold-dim);letter-spacing:0.02em;transition:all .18s;" onmouseover="this.style.background='rgba(232,167,76,0.22)'" onmouseout="this.style.background='var(--gold-dim)'">🧠 3D 大脑图谱 →</a>
  <div class="search-wrap">
    <input class="search-input" type="text" placeholder="搜索知识点..." id="searchInput">
  </div>
  <div class="nav-count" id="navCount">共 {count} 个知识点</div>
  <ul class="nav-list" id="navList">
{sidebar_items}
  </ul>
</aside>

<main class="main" id="mainArea">
  <!-- 欢迎页 -->
  <div class="welcome" id="welcomePage">
    <div class="welcome-icon">🧠</div>
    <h1>Brain Knowledge</h1>
    <p>关于大脑、元认知与认知科学的系统笔记<br>点击左侧知识点开始阅读</p>
    <div class="welcome-stats">
      <div class="stat">
        <div class="stat-num">{count}</div>
        <div class="stat-label">知识点</div>
      </div>
      <div class="stat">
        <div class="stat-num">∞</div>
        <div class="stat-label">持续更新</div>
      </div>
    </div>
  </div>

  <!-- 文章展示区 -->
  <div class="article-page" id="articlePage">
    <div class="article-header">
      <div class="article-date" id="articleDate"></div>
      <h1 class="article-title" id="articleTitle"></h1>
    </div>
    <div class="article-body" id="articleBody"></div>
  </div>

  <div class="no-result" id="noResult">没有找到相关知识点</div>
</main>

<script>
const ENTRIES = {entries_json};

const searchInput = document.getElementById('searchInput');
const navList     = document.getElementById('navList');
const navCount    = document.getElementById('navCount');
const noResult    = document.getElementById('noResult');
const welcomePage = document.getElementById('welcomePage');
const articlePage = document.getElementById('articlePage');
const articleDate  = document.getElementById('articleDate');
const articleTitle = document.getElementById('articleTitle');
const articleBody  = document.getElementById('articleBody');

let activeId = null;

// marked 配置
marked.setOptions({{ breaks: true, gfm: true }});

function showEntry(id) {{
  const entry = ENTRIES.find(e => e.id === id);
  if (!entry) return;
  activeId = id;

  welcomePage.style.display = 'none';
  articlePage.classList.add('visible');
  noResult.style.display = 'none';

  articleDate.textContent = entry.date ? '更新时间：' + entry.date : '';
  articleTitle.textContent = entry.title;
  articleBody.innerHTML = marked.parse(entry.content);

  // 更新导航高亮
  document.querySelectorAll('.nav-link').forEach(a => {{
    a.classList.toggle('active', a.dataset.id === id);
  }});

  articlePage.scrollTop = 0;
}}

// 搜索过滤
searchInput.addEventListener('input', () => {{
  const q = searchInput.value.trim().toLowerCase();
  const items = navList.querySelectorAll('li');
  let visible = 0;
  items.forEach(li => {{
    const link = li.querySelector('.nav-link');
    const title = link.textContent.toLowerCase();
    const entry = ENTRIES.find(e => e.id === link.dataset.id);
    const match = !q || title.includes(q) || (entry && entry.content.toLowerCase().includes(q));
    li.style.display = match ? '' : 'none';
    if (match) visible++;
  }});
  navCount.textContent = '共 ' + visible + ' 个知识点';
  noResult.style.display = (visible === 0 && q) ? 'block' : 'none';
}});

// 默认显示第一条
if (ENTRIES.length > 0) {{
  showEntry(ENTRIES[0].id);
}}
</script>
</body>
</html>"""
    return html

def main():
    entries = read_md_files()
    if not entries:
        print("没有找到任何 .md 文件")
        return
    html = build_html(entries)
    out = BASE_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"构建完成：{out}")
    print(f"共 {len(entries)} 个知识点：" + "、".join(e['title'] for e in entries))

if __name__ == "__main__":
    main()
