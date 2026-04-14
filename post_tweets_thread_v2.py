#!/usr/bin/env python3
"""
长链 Thread 生成器（v2）
把笔记内容转换成一个完整的论述链，每条推文独立完整，但串成一个故事
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

def clean_markdown_and_tables(text):
    """去除所有 Markdown 和表格符号"""
    # 去除粗体、斜体、代码
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\1', text)
    text = re.sub(r'`([^`]+?)`', r'\1', text)
    text = re.sub(r'\[([^\]]+?)\]\([^\)]+?\)', r'\1', text)

    # 去除表格符号
    text = re.sub(r'\|[^\n]*\|', '', text)
    text = re.sub(r'[-:]+[-:\s|]*', '', text)

    # 去除列表符号但保留内容
    lines = []
    for line in text.split('\n'):
        line = re.sub(r'^[\s]*[-*+]\s+', '', line)
        if line.strip():
            lines.append(line.strip())

    return ' '.join(lines).strip()

def extract_full_text(file_path):
    """提取笔记的核心内容（不分块，作为一个完整论述）"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取标题
    title_match = re.match(r'# (.+?)(?:\n|$)', content)
    title = title_match.group(1) if title_match else '知识点'

    # 按 ## 二级标题分块，构建论述链
    sections = re.split(r'\n## ', content)

    threads = []
    sources = []

    # 提取来源
    for line in content.split('\n'):
        if line.startswith('- ['):
            match = re.match(r'- \[([^\]]+)\]', line)
            if match:
                name = match.group(1)
                if '|' in name:
                    name = name.split('|')[-1].strip()
                name = name[:20]
                sources.append(name)

    if not sources:
        sources = ['研究', '科学', '理论']

    # 遍历各个段落，构建推文
    for i, section in enumerate(sections[1:]):  # 跳过标题
        lines = section.strip().split('\n')
        sec_title = lines[0].strip()

        # 跳过不需要的部分
        if sec_title in {'参考来源', '参考文献', '标签', '相关概念'}:
            continue

        # 提取段落正文
        body_lines = []
        for line in lines[1:]:
            if line.startswith('---'):
                break
            # 跳过三级标题但记录内容
            if line.startswith('### '):
                continue
            if line.startswith('#### '):
                continue
            if line.strip() and not line.startswith('#'):
                body_lines.append(line.strip())

        body = ' '.join(body_lines)
        body = clean_markdown_and_tables(body)

        # 剪裁到 250 字以内（留空间给序号和来源）
        if len(body) > 250:
            body = body[:250]
            # 找最后一个句号截断
            last_period = body.rfind('。')
            if last_period > 200:
                body = body[:last_period + 1]
            else:
                body = body.rstrip('，') + '...'

        if body and len(body) > 30:
            # 添加序号和小标题
            tweet = f'【{title}】({i+1})\n\n{sec_title}\n\n{body}'
            source = sources[i % len(sources)]
            threads.append((tweet, source))

    return threads

def post_tweet_thread(threads):
    """发送 Thread"""
    if not threads:
        print('❌ 未能提取推文')
        return False

    print(f'开始发送 {len(threads)} 条 Thread...\n')

    last_tweet_id = None
    success_count = 0

    for i, (tweet_text, source) in enumerate(threads, 1):
        # 添加来源
        full_text = f'{tweet_text}\n— {source}'

        # 确保不超过 280 字
        if len(full_text) > 280:
            # 截短正文
            body_start = tweet_text.find('\n\n') + 2
            body_end = tweet_text.rfind('\n')
            body = tweet_text[body_start:body_end]

            if len(body) > 100:
                body = body[:100].rstrip('，。') + '...'

            title_and_sub = tweet_text[:body_start]
            full_text = f'{title_and_sub}{body}\n— {source}'

        try:
            if last_tweet_id:
                response = client.create_tweet(
                    text=full_text,
                    in_reply_to_tweet_id=last_tweet_id
                )
            else:
                response = client.create_tweet(text=full_text)

            last_tweet_id = response.data['id']
            print(f'✅ {i}/{len(threads)} 成功 (ID: {last_tweet_id})')
            print(f'   {full_text[:60]}...\n')
            success_count += 1

        except Exception as e:
            print(f'❌ {i}/{len(threads)} 失败: {e}')
            last_tweet_id = None

    print(f'\n完成！成功发送 {success_count}/{len(threads)} 条推文')
    return success_count == len(threads)

def main():
    if len(sys.argv) < 2:
        print('用法: python3 post_tweets_thread_v2.py <知识点名称>')
        sys.exit(1)

    knowledge_name = sys.argv[1]
    file_name = knowledge_name.replace(' ', '_') + '.md'
    file_path = Path(__file__).parent / file_name

    if not file_path.exists():
        print(f'❌ 文件不存在: {file_path}')
        sys.exit(1)

    threads = extract_full_text(file_path)
    post_tweet_thread(threads)

if __name__ == '__main__':
    main()
