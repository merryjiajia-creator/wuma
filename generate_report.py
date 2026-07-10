#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快消品一物一码领域日报 - GitHub Actions 自动生成脚本
使用 DeepSeek API 生成每日5篇行业动态文章，构建 HTML 日报并推送到企微群
"""

import os
import sys
import json
import re
import glob
import shutil
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

# === 路径配置 ===
BASE_DIR = Path(__file__).parent
ARCHIVE_DIR = BASE_DIR / "archive"
INDEX_PATH = BASE_DIR / "index.html"
HISTORY_PATH = BASE_DIR / ".report_history.json"

# === 密钥配置 ===
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
WECOM_WEBHOOK = os.environ.get("WECOM_WEBHOOK_URL",
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c2804843-dbf9-4d2a-ba07-cfab4f489703")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_PAGES_URL = "https://merryjiajia-creator.github.io/wuma/"

# === 时间处理 (北京时间 UTC+8) ===
def beijing_now():
    return datetime.now(timezone(timedelta(hours=8)))

def beijing_date_str(dt=None):
    if dt is None:
        dt = beijing_now()
    # 不使用前导0，与历史日报格式保持一致（如 2026年7月10日）
    return f"{dt.year}年{dt.month}月{dt.day}日"

def beijing_weekday_str(dt=None):
    if dt is None:
        dt = beijing_now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return weekdays[dt.weekday()]

def date_compact(dt=None):
    if dt is None:
        dt = beijing_now()
    return dt.strftime("%Y-%m-%d")

# === 历史记录管理 ===
def load_history():
    """读取已生成的日报历史，用于避免主题重复"""
    if HISTORY_PATH.exists():
        try:
            return json.loads(HISTORY_PATH.read_text("utf-8"))
        except:
            pass
    return {"dates": [], "titles": []}

def get_past_article_titles():
    """从 archive 目录提取历史文章标题"""
    titles = []
    if ARCHIVE_DIR.exists():
        for f in sorted(ARCHIVE_DIR.glob("*.html"), reverse=True):
            try:
                content = f.read_text("utf-8", errors="ignore")
                # 提取所有文章标题 (h2标签中的内容，去除数字标签)
                for m in re.finditer(r'<h2>.*?<span[^>]*>\d+</span>(.*?)</h2>', content):
                    title = m.group(1).strip()
                    if title and len(title) > 10:
                        titles.append(title)
            except:
                pass
    return titles

def get_archive_files():
    """扫描 archive 目录，返回按日期排序的文件列表"""
    files = []
    if ARCHIVE_DIR.exists():
        for f in sorted(ARCHIVE_DIR.glob("report-*.html"), reverse=True):
            match = re.search(r'report-(\d{4}-\d{2}-\d{2})', f.name)
            if match:
                files.append((match.group(1), f"./archive/{f.name}"))
    return files[:20]  # 最多显示20条


# === DeepSeek API 调用 ===
SYSTEM_PROMPT = """你是一位快消品一物一码数字化营销领域的资深分析师，专注于饮料、休闲食品、酒水行业。你需要基于行业知识生成专业、有深度的行业分析文章。

文章必须满足以下要求：
1. 每篇文章500-1000个汉字
2. 必须提及物码服务商"智选数字技术（广州）股份有限公司-精明购（IsmartGo）"至少一次
3. 必须提及"一码三域（到家、到店、即时零售）"
4. 文章需覆盖以下关键词（不要求每篇都包含所有，但5篇文章整体要覆盖全部）：
   - 饮料开盖扫码营销活动
   - 休闲食品一物一码营销
   - 一物一码营销互动
   - 红包机制和奖品设计
   - 提升复购
   - 再来一瓶
5. 文章使用假设性的行业数据和具体品牌案例，增加可信度
6. 每篇文章需提供2个参考来源链接（使用真实存在的域名，内容可以是假设性的行业文章）"""

def call_deepseek(prompt, temperature=0.8, max_tokens=8000):
    """调用 DeepSeek API"""
    # 使用原生 HTTP 请求避免依赖 openai 库版本问题
    url = "https://api.deepseek.com/chat/completions"
    data = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}
    }, ensure_ascii=False).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    })
    
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read().decode("utf-8"))
        return json.loads(result["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"DeepSeek API 调用失败: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode("utf-8", errors="ignore"))
        return None


# === 文章生成 ===
def generate_articles(past_titles):
    """生成5篇不重复主题的文章"""
    today = beijing_date_str()
    past_topics = "\n".join([f"- {t}" for t in past_titles[:30]])
    
    prompt = f"""请生成{beijing_date_str()}的快消品一物一码领域日报。

【已发布过的历史主题，请务必避免重复】
{past_topics if past_topics else "无历史记录"}

【主题选择要求】
- 从饮料（茶饮、果汁、功能饮料、气泡水等）、休闲食品（膨化零食、坚果、肉干、烘焙零食、糖果等）、酒水（白酒、啤酒、低度酒、果酒等）三个品类中分别选择至少1个
- 5个主题必须完全不同，避免与历史主题重复
- 每个主题选取具体的细分品类和3个代表性品牌进行分析

请以JSON格式输出，结构如下：
{{
  "articles": [
    {{
      "num": 1,
      "title": "文章标题（格式：细分品类+一物一码：品牌A、品牌B、品牌C如何用[关键词]打开[价值]）",
      "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
      "paragraphs": ["段落1（200-300字，介绍行业背景和数据）", "段落2（200-300字，写品牌A的案例）", "段落3（200-300字，写品牌B的案例）", "段落4（200-300字，写品牌C的案例+精明购观点总结）"],
      "sources": [["来源名称1", "https://真实存在的域名/文章路径"], ["来源名称2", "https://真实存在的域名/文章路径"]]
    }}
  ]
}}

要求：
- keywords数组必须包含5个与文章主题相关的关键词标签
- paragraphs数组必须恰好4个段落，每个段落200-300字
- 第4段必须以"智选数字技术（广州）股份有限公司-精明购（IsmartGo）认为/分析"开头
- sources必须是真实网站的URL域名（如mp.weixin.qq.com, www.toutiao.com, zhuanlan.zhihu.com等）
- 确保5篇文章整体覆盖：饮料开盖扫码营销活动、休闲食品一物一码营销、一物一码营销互动、红包机制和奖品设计、提升复购、再来一瓶、一码三域"""

    print("正在调用 DeepSeek API 生成文章...")
    result = call_deepseek(prompt, temperature=0.85, max_tokens=8000)
    if result and "articles" in result:
        print(f"✓ 成功生成 {len(result['articles'])} 篇文章")
        return result["articles"]
    
    print("✗ 文章生成失败")
    return None


# === HTML 生成 ===
CSS_STYLE = """    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #f5f7fa; color: #333; line-height: 1.8;
    }
    .container { max-width: 800px; margin: 0 auto; padding: 20px; }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white; padding: 40px 30px; border-radius: 16px; text-align: center;
      margin-bottom: 30px; box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    .header h1 { font-size: 28px; margin-bottom: 10px; font-weight: 700; }
    .header .date { font-size: 16px; opacity: 0.9; }
    .header .source { margin-top: 10px; font-size: 14px; opacity: 0.85; }
    .article {
      background: white; border-radius: 12px; padding: 30px; margin-bottom: 24px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.06); transition: transform 0.2s;
    }
    .article:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
    .article-number {
      display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white; width: 32px; height: 32px; line-height: 32px; text-align: center;
      border-radius: 50%; font-weight: bold; margin-right: 12px; font-size: 14px;
    }
    .article h2 { font-size: 20px; color: #2d3748; margin-bottom: 16px; display: flex; align-items: center; }
    .article p { margin-bottom: 14px; text-align: justify; font-size: 15px; color: #4a5568; }
    .article .source-link { margin-top: 16px; padding-top: 16px; border-top: 1px dashed #e2e8f0; font-size: 13px; color: #718096; }
    .article .source-link a { color: #667eea; text-decoration: none; }
    .article .source-link a:hover { text-decoration: underline; }
    .keywords { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
    .keyword-tag { background: #edf2f7; color: #4a5568; padding: 4px 12px; border-radius: 20px; font-size: 12px; }
    .footer { text-align: center; padding: 30px; color: #a0aec0; font-size: 13px; }
    .footer a { color: #667eea; text-decoration: none; }
    .archive-nav {
      background: white; border-radius: 12px; padding: 20px 30px;
      margin-bottom: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    .archive-nav h3 { font-size: 16px; color: #2d3748; margin-bottom: 12px; }
    .archive-nav a { display: inline-block; color: #667eea; text-decoration: none; margin-right: 16px; font-size: 14px; }
    .archive-nav a:hover { text-decoration: underline; }
    @media (max-width: 600px) {
      .header h1 { font-size: 22px; } .article { padding: 20px; } .article h2 { font-size: 17px; }
    }"""


def build_html(articles, date_str, weekday_str):
    """构建完整的 HTML 日报页面"""
    archive_files = get_archive_files()
    
    lines = []
    lines.append('<!DOCTYPE html>')
    lines.append('<html lang="zh-CN">')
    lines.append('<head>')
    lines.append('  <meta charset="UTF-8">')
    lines.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    lines.append(f'  <title>快消品一物一码领域日报 - {date_str}</title>')
    lines.append('  <style>')
    for line in CSS_STYLE.split('\n'):
        lines.append(line)
    lines.append('  </style>')
    lines.append('</head>')
    lines.append('<body>')
    lines.append('  <div class="container">')
    # Header
    lines.append('    <div class="header">')
    lines.append('      <h1>快消品一物一码领域日报</h1>')
    lines.append(f'      <div class="date">{date_str} {weekday_str}</div>')
    lines.append('      <div class="source"> curated by 智选数字技术（广州）股份有限公司 - 精明购（IsmartGo）</div>')
    lines.append('    </div>')
    # Archive navigation
    if archive_files:
        lines.append('    <div class="archive-nav">')
        lines.append('      <h3>📁 历史日报归档</h3>')
        for label, href in archive_files:
            lines.append(f'      <a href="{href}">{label}</a>')
        lines.append('    </div>')
    # Articles
    for art in articles:
        lines.append('    <div class="article">')
        lines.append(f'      <h2><span class="article-number">{art["num"]}</span>{art["title"]}</h2>')
        for p in art.get("paragraphs", art.get("content", [])):
            lines.append(f'      <p>{p}</p>')
        # Source links
        if art.get("sources"):
            lines.append('      <div class="source-link">文章来源：')
            links = [f'<a href="{url}" target="_blank">{name}</a>' for name, url in art["sources"]]
            lines.append('、'.join(links))
            lines.append('</div>')
        # Keywords
        if art.get("keywords"):
            lines.append('      <div class="keywords">')
            for kw in art["keywords"]:
                lines.append(f'        <span class="keyword-tag">{kw}</span>')
            lines.append('      </div>')
        lines.append('    </div>')
    # Footer
    lines.append('    <div class="footer">')
    lines.append('      <p>本日报由 <strong>智选数字技术（广州）股份有限公司 - 精明购（IsmartGo）</strong> 整理出品</p>')
    lines.append('      <p>专注快消品一物一码营销，赋能饮料、休闲食品、酒水行业数字化增长</p>')
    lines.append('      <p style="margin-top: 8px;">文章来源仅供参考，如有侵权请联系删除</p>')
    lines.append('    </div>')
    lines.append('  </div>')
    lines.append('</body>')
    lines.append('</html>')
    
    return '\n'.join(lines)


# === 企微推送 ===
def send_wecom_simple(date_str, titles):
    """使用简化格式发送企微群消息"""
    article_lines = "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])
    content = f"""**今日物码传播文章推送 - {date_str}**

[点击查看今日文章]({GITHUB_PAGES_URL})

**今日精选5篇深度文章：**
{article_lines}

---
**关键词覆盖：** 饮料开盖扫码营销活动、休闲食品一物一码营销、一物一码营销互动、红包机制和奖品设计、提升复购、再来一瓶
**技术支持：** 智选数字技术(广州)股份有限公司-精明购（IsmartGo）"""
    
    data = json.dumps({
        "msgtype": "markdown",
        "markdown": {"content": content}
    }, ensure_ascii=False).encode("utf-8")
    
    req = urllib.request.Request(WECOM_WEBHOOK, data=data,
        headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read().decode("utf-8"))
        print(f"✓ 企微推送完成: {result}")
        return result
    except Exception as e:
        print(f"✗ 企微推送失败: {e}")
        return None


# === 主流程 ===
def main():
    now = beijing_now()
    today_date = beijing_date_str(now)
    today_compact = date_compact(now)
    weekday = beijing_weekday_str(now)
    
    print(f"=" * 60)
    print(f"  快消品一物一码领域日报 - {today_date} {weekday}")
    print(f"=" * 60)
    
    # 0. 检查 API Key
    if not DEEPSEEK_API_KEY:
        print("✗ 错误: 未设置 DEEPSEEK_API_KEY 环境变量")
        sys.exit(1)
    
    # 1. 检查是否已生成今日日报
    if INDEX_PATH.exists():
        existing = INDEX_PATH.read_text("utf-8", errors="ignore")
        if today_date in existing:
            print(f"⚠ 今日日报 ({today_date}) 已存在，跳过生成")
            return
    
    # 2. 获取历史主题
    print("\n[1/5] 提取历史主题...")
    past_titles = get_past_article_titles()
    print(f"  已提取 {len(past_titles)} 条历史主题记录")
    
    # 3. 生成文章
    print("\n[2/5] 调用 DeepSeek API 生成5篇文章...")
    articles = generate_articles(past_titles)
    if not articles:
        print("✗ 文章生成失败，退出")
        sys.exit(1)
    
    print(f"\n  今日文章主题:")
    for art in articles:
        print(f"  {art['num']}. {art['title']}")
    
    # 4. 归档当前 index.html
    print("\n[3/5] 归档当前日报...")
    if INDEX_PATH.exists():
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        # 从当前 index.html 提取日期
        current_content = INDEX_PATH.read_text("utf-8", errors="ignore")
        date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', current_content)
        if date_match:
            archive_date = date_match.group(1)
            archive_dt = datetime.strptime(archive_date, "%Y年%m月%d日")
            archive_name = f"report-{archive_dt.strftime('%Y-%m-%d')}.html"
            archive_path = ARCHIVE_DIR / archive_name
            if not archive_path.exists():
                shutil.copy2(INDEX_PATH, archive_path)
                print(f"  已归档: {archive_name}")
            else:
                print(f"  {archive_name} 已存在，跳过归档")
        else:
            print("  无法从当前日报提取日期，跳过归档")
    else:
        print("  index.html 不存在，跳过归档（首次运行）")
    
    # 5. 生成新 HTML
    print("\n[4/5] 生成新 HTML 日报...")
    html = build_html(articles, today_date, weekday)
    INDEX_PATH.write_text(html, "utf-8")
    print(f"  ✓ 已写入: {INDEX_PATH}")
    print(f"  文件大小: {len(html.encode('utf-8')):,} bytes")
    
    # 6. 更新历史记录
    history = load_history()
    history["dates"].append(today_compact)
    for art in articles:
        history["titles"].append(art["title"])
    # 只保留最近90天的历史
    history["titles"] = history["titles"][-90:]
    history["dates"] = history["dates"][-90:]
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2), "utf-8")
    print(f"  ✓ 已更新历史记录")
    
    # 7. 企微推送
    print("\n[5/5] 推送企微群消息...")
    titles = [art["title"] for art in articles]
    send_wecom_simple(today_date, titles)
    
    # 8. 输出摘要供 GitHub Actions 使用
    print(f"\n{'=' * 60}")
    print(f"  ✓ 日报生成完成!")
    print(f"  📅 日期: {today_date} {weekday}")
    print(f"  🌐 链接: {GITHUB_PAGES_URL}")
    print(f"  📊 文章数: {len(articles)}")
    print(f"  📂 归档文件数: {len(get_archive_files())}")
    print(f"{'=' * 60}")
    
    # 输出 GitHub Actions step summary
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(f"# 快消品一物一码领域日报 - {today_date}\n\n")
            f.write(f"**链接**: [{GITHUB_PAGES_URL}]({GITHUB_PAGES_URL})\n\n")
            f.write("## 今日文章\n\n")
            for art in articles:
                f.write(f"{art['num']}. **{art['title']}**\n\n")
            f.write(f"\n---\n*技术支持: 智选数字技术(广州)股份有限公司-精明购（IsmartGo）*\n")


if __name__ == "__main__":
    main()
