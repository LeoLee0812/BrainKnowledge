#!/usr/bin/env python3
"""
多推文线程发送器
根据笔记内容自动拆分成核心观点 + 论据的推文，逐条发送
"""

import json
import re
import tweepy
import sys
from pathlib import Path

config_path = Path.home() / '.claude' / 'config' / 'twitter_oauth2.json'
with open(config_path) as f:
    config = json.load(f)

client = tweepy.Client(
    consumer_key=config['consumer_key'],
    consumer_secret=config['consumer_secret'],
    access_token=config['access_token'],
    access_token_secret=config['access_token_secret']
)

def clean_markdown(text):
    """去除 Markdown 格式"""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\1', text)
    text = re.sub(r'`([^`]+?)`', r'\1', text)
    text = re.sub(r'\[([^\]]+?)\]\([^\)]+?\)', r'\1', text)
    return text.strip()

def extract_tweet_threads(file_path):
    """
    通用版：按 ## 二级标题自动分块，每块生成一条推文
    返回：[(推文内容, 论据来源), ...]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取参考来源列表（用于论据，只取期刊/书名，不含URL片段）
    sources = []
    sources_match = re.search(r'## 参考来源\n\n(.*?)(?:\n\n---|\Z)', content, re.DOTALL)
    if sources_match:
        raw_sources = sources_match.group(1)
        for line in raw_sources.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            # 提取 markdown 链接中的文字
            link_match = re.match(r'[-*]?\s*\[([^\]]+)\]', line)
            if link_match:
                name = link_match.group(1)
            elif line.startswith('-') or line.startswith('*'):
                name = line.lstrip('-* ')
            else:
                continue
            # 只取期刊名/机构名（最后一个 | 后面的，或前20字）
            if '|' in name:
                name = name.split('|')[-1].strip()
            name = name[:25]
            if name:
                sources.append(name)

    # 按 ## 二级标题分块
    sections = re.split(r'\n## ', content)
    threads = []
    skip_titles = {'参考来源', '参考文献', '相关概念', '深层反思', '标签'}

    for section in sections[1:]:  # 跳过第一块（标题+日期）
        lines = section.strip().split('\n')
        title = lines[0].strip()

        # 跳过不需要发推的部分
        if title in skip_titles:
            continue

        # 提取正文（去除 ### 三级标题，保留内容）
        body_lines = []
        for line in lines[1:]:
            if line.startswith('---'):
                break
            # 保留三级标题内容但简化格式
            if line.startswith('### '):
                body_lines.append(line.replace('### ', '').strip() + ':')
            elif line.startswith('#### '):
                continue  # 跳过四级标题
            elif line.strip():
                body_lines.append(line.strip())

        body = ' '.join(body_lines)
        body = clean_markdown(body)
        body = re.sub(r'\s+', ' ', body).strip()

        if not body or len(body) < 20:
            continue

        # 截断到230字符（留空间给标题和来源）
        if len(body) > 220:
            body = body[:220] + '...'

        # 匹配一个来源
        source = sources[len(threads) % len(sources)] if sources else '神经科学研究'
        # 截取来源名（最多30字）
        source = source[:30]

        tweet_text = f'{title}\n\n{body}'
        threads.append((tweet_text, source))

    return threads

def post_tweet_thread(threads):
    """发送推文线程（每条回复上一条，串成 Thread）"""
    if not threads:
        print('❌ 未能提取推文线程')
        return False

    print(f'开始发送 {len(threads)} 条推文（Thread 模式）...\n')

    success_count = 0
    last_tweet_id = None  # 追踪上一条推文的 ID

    for i, (tweet_text, source) in enumerate(threads, 1):
        # 添加来源
        full_text = f'{tweet_text}\n— {source}'

        # 确保不超过280字符
        if len(full_text) > 280:
            tweet_text = tweet_text[:200]
            full_text = f'{tweet_text}...\n— {source}'

        try:
            # 第一条正常发，后续每条都回复上一条
            if last_tweet_id:
                response = client.create_tweet(
                    text=full_text,
                    in_reply_to_tweet_id=last_tweet_id
                )
            else:
                response = client.create_tweet(text=full_text)

            last_tweet_id = response.data['id']
            print(f'✅ 推文 {i}/{len(threads)} 发送成功 (ID: {last_tweet_id})')
            success_count += 1
        except Exception as e:
            print(f'❌ 推文 {i} 失败: {e}')
            last_tweet_id = None  # 失败后断开链接

    print(f'\n完成！成功发送 {success_count}/{len(threads)} 条推文（已串成 Thread）')
    return success_count == len(threads)

def main():
    if len(sys.argv) < 2:
        print('用法: python3 post_tweets_thread.py <知识点名称>')
        sys.exit(1)

    knowledge_name = sys.argv[1]
    file_name = knowledge_name.replace(' ', '_') + '.md'
    file_path = Path(__file__).parent / file_name

    if not file_path.exists():
        print(f'❌ 文件不存在: {file_path}')
        sys.exit(1)

    threads = extract_tweet_threads(file_path)
    post_tweet_thread(threads)

if __name__ == '__main__':
    main()
