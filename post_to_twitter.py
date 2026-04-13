#!/usr/bin/env python3
import json
import re
import tweepy
import sys
from pathlib import Path
from urllib.parse import quote

# 读取Twitter凭证
config_path = Path.home() / '.claude' / 'config' / 'twitter_oauth2.json'
with open(config_path) as f:
    config = json.load(f)

CONSUMER_KEY = config['consumer_key']
CONSUMER_SECRET = config['consumer_secret']
ACCESS_TOKEN = config['access_token']
ACCESS_TOKEN_SECRET = config['access_token_secret']

def post_tweet(text):
    """发送推文（使用 tweepy OAuth 1.0a）"""
    try:
        # 初始化客户端
        client = tweepy.Client(
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )

        # 发送推文
        response = client.create_tweet(text=text)
        tweet_id = response.data['id']
        print(f"✅ 推文已发送 (ID: {tweet_id}): {text[:50]}...")
        return True

    except tweepy.TweepyException as e:
        print(f"❌ 发推失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def clean_markdown(text):
    """去除 Markdown 格式符号"""
    # 去除粗体 **xxx**
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # 去除斜体 *xxx*
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\1', text)
    # 去除内联代码 `xxx`
    text = re.sub(r'`([^`]+?)`', r'\1', text)
    # 去除链接 [xxx](yyy)
    text = re.sub(r'\[([^\]]+?)\]\([^\)]+?\)', r'\1', text)
    return text.strip()

def extract_summary(file_path):
    """从Markdown笔记提取摘要"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取标题（去除冒号等特殊符号）
    lines = content.split('\n')
    title = lines[0].replace('# ', '').strip()
    title = clean_markdown(title)

    # 提取定义和背景部分
    summary_start = content.find('## 定义与背景')
    if summary_start != -1:
        summary_end = content.find('##', summary_start + 1)
        summary = content[summary_start:summary_end].replace('## 定义与背景\n', '').strip()
        summary = clean_markdown(summary)[:120]
    else:
        summary = ''

    return title, summary

def main():
    if len(sys.argv) < 2:
        print("用法: python3 post_to_twitter.py <知识点名称>")
        sys.exit(1)

    knowledge_name = sys.argv[1]
    file_name = knowledge_name.replace(' ', '_') + '.md'
    file_path = Path(__file__).parent / file_name

    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    title, summary = extract_summary(file_path)

    # URL 编码文件名（避免中文 URL 问题）
    encoded_name = quote(file_name)
    github_url = f"https://github.com/superlls/BrainKnowledge/blob/main/{encoded_name}"

    # 先试试完整版本
    tweet_text = f"""🧠 新笔记：{title}

{summary}

完整内容: {github_url}"""

    # 如果超过280字符就缩短
    if len(tweet_text) > 280:
        summary = summary[:80]
        tweet_text = f"""🧠 {title}

{summary}...

{github_url}"""

    post_tweet(tweet_text)

if __name__ == '__main__':
    main()
