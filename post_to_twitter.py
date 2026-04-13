#!/usr/bin/env python3
import json
import requests
import sys
import os
from pathlib import Path

# 读取Twitter凭证
config_path = Path.home() / '.claude' / 'config' / 'twitter_oauth2.json'
with open(config_path) as f:
    config = json.load(f)

CLIENT_ID = config['client_id']
CLIENT_SECRET = config['client_secret']

def get_access_token():
    """获取Twitter OAuth2访问令牌"""
    auth_url = "https://api.twitter.com/2/oauth2/token"

    auth = (CLIENT_ID, CLIENT_SECRET)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials"
    }

    response = requests.post(auth_url, auth=auth, headers=headers, data=data)
    response.raise_for_status()
    return response.json()['access_token']

def post_tweet(text):
    """发送推文"""
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {"text": text}

    response = requests.post(
        "https://api.twitter.com/2/tweets",
        headers=headers,
        json=data
    )

    if response.status_code == 201:
        print(f"✅ 推文已发送: {text[:50]}...")
        return True
    else:
        print(f"❌ 发推失败: {response.status_code} - {response.text}")
        return False

def extract_summary(file_path):
    """从Markdown笔记提取摘要"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取标题
    lines = content.split('\n')
    title = lines[0].replace('# ', '').strip()

    # 提取定义和背景部分（前150字）
    summary_start = content.find('## 定义与背景')
    if summary_start != -1:
        summary_end = content.find('##', summary_start + 1)
        summary = content[summary_start:summary_end].replace('## 定义与背景\n', '').strip()[:150]
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

    # 构造推文（Twitter限制280字符）
    github_url = f"https://github.com/superlls/BrainKnowledge/blob/main/{file_name}"
    tweet_text = f"""🧠 新笔记：{title}

{summary}

完整内容: {github_url}"""

    # 确保不超过280字符
    if len(tweet_text) > 280:
        summary = summary[:100]  # 缩短摘要
        tweet_text = f"""🧠 {title}

{summary}...

{github_url}"""

    post_tweet(tweet_text)

if __name__ == '__main__':
    main()
