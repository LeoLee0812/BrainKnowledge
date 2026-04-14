#!/usr/bin/env python3
"""
长链 Thread 生成器（v3）
- 每个 ## 二级标题 = 一条推文
- 充分利用 280 字符，内容完整不截断
- 只在最后一条加来源
"""

import json
import re
import tweepy
import sys
import time
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

def clean_text(text):
    """清理 Markdown 格式，保留内容（包括表格内容）"""
    # 去除粗体、斜体、代码
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\1', text)
    text = re.sub(r'`([^`]+?)`', r'\1', text)
    text = re.sub(r'\[([^\]]+?)\]\([^\)]+?\)', r'\1', text)

    # 清理表格：提取表格内容
    # 表格格式: | 内容 | 内容 |，提取 | 中间的文字
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # 如果是表格行（含 |）
        if '|' in line and not re.match(r'^[\s]*[-:\|]+[\s]*$', line):
            # 提取 | 之间的内容
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            cleaned_lines.extend([c for c in cells if c])
        else:
            # 非表格行
            # 去除列表符号
            line = re.sub(r'^[\s]*[-*+]\s+', '', line)
            line = line.strip()
            if line and not line.startswith('#'):
                cleaned_lines.append(line)

    # 合并成一行，保留适当空格
    result = ' '.join(cleaned_lines)
    # 去除多余空格
    result = re.sub(r'\s+', ' ', result).strip()
    return result

def extract_sections(file_path):
    """
    提取所有 ## 二级标题的内容
    返回: [(标题, 内容), ...]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取文件标题
    title_match = re.match(r'# (.+?)(?:\n|$)', content)
    main_title = title_match.group(1) if title_match else '知识点'

    # 提取来源（用于最后一条）
    sources = []
    for line in content.split('\n'):
        if line.startswith('- ['):
            match = re.match(r'- \[([^\]]+)\]', line)
            if match:
                name = match.group(1)
                if '|' in name:
                    name = name.split('|')[-1].strip()
                name = name[:25]
                sources.append(name)

    source_text = sources[0] if sources else '研究'

    # 按 ## 分割
    sections = re.split(r'\n## ', content)

    threads = []

    for i, section in enumerate(sections[1:], 1):  # 跳过第一块（标题）
        lines = section.strip().split('\n')
        sec_title = lines[0].strip()

        # 跳过不需要发推的部分
        if sec_title in {'参考来源', '参考文献', '标签', '相关概念', '深层反思'}:
            continue

        # 提取该部分的所有内容（跳过三级标题，保留正文）
        body_lines = []
        for line in lines[1:]:
            if line.startswith('---'):
                break
            # 跳过三级、四级标题
            if line.startswith('### ') or line.startswith('#### '):
                continue
            if line.strip():
                body_lines.append(line.strip())

        # 清理文本
        body = '\n'.join(body_lines)
        body = clean_text(body)

        if not body or len(body) < 20:
            continue

        # 构建推文：标题(序号) + 小标题 + 内容
        # 留出 20 字给 markdown 格式符号
        available_chars = 260  # 280 - 20 for safety

        # 计算标题占用的字符数
        title_line = f'【{main_title}】({i})\n\n'
        subtitle_line = f'{sec_title}\n\n'
        header_chars = len(title_line) + len(subtitle_line)

        # 剩余给内容的字符数
        content_chars = available_chars - header_chars

        # 如果内容超长，优先保留完整句子
        if len(body) > content_chars:
            # 尝试在句号处截断
            truncated = body[:content_chars]
            last_period = truncated.rfind('。')
            if last_period > content_chars - 50:  # 在合理范围内
                body = body[:last_period + 1]
            else:
                # 否则在逗号处截断
                last_comma = truncated.rfind('，')
                if last_comma > content_chars - 50:
                    body = body[:last_comma + 1]
                else:
                    body = truncated.rstrip('，。') + '...'

        # 构建完整推文
        tweet_text = f'{title_line}{subtitle_line}{body}'

        threads.append((tweet_text, sec_title, i))

    # 添加来源到最后一条
    if threads:
        last_text, last_sub, last_num = threads[-1]
        # 在最后一条后加来源
        threads[-1] = (f'{last_text}\n\n— {source_text}', last_sub, last_num)

    return threads

def post_tweet_thread(threads):
    """发送 Thread（带延迟防止速率限制）"""
    if not threads:
        print('❌ 未能提取推文')
        return False

    print(f'开始发送 {len(threads)} 条 Thread（每条间隔 30 秒）...\n')

    last_tweet_id = None
    success_count = 0

    for i, (tweet_text, subtitle, seq_num) in enumerate(threads, 1):
        # 确保不超过 280 字
        if len(tweet_text) > 280:
            print(f'⚠️  推文 {i} 超长 ({len(tweet_text)} 字)，自动截断')
            tweet_text = tweet_text[:277] + '...'

        # 失败重试机制
        max_retries = 2
        retry_count = 0
        success = False

        while retry_count <= max_retries and not success:
            try:
                if last_tweet_id:
                    response = client.create_tweet(
                        text=tweet_text,
                        in_reply_to_tweet_id=last_tweet_id
                    )
                else:
                    response = client.create_tweet(text=tweet_text)

                last_tweet_id = response.data['id']
                print(f'✅ {i}/{len(threads)} 成功 (ID: {last_tweet_id})')
                print(f'   {tweet_text[:70]}...')
                success_count += 1
                success = True

                # 成功后等待 60 秒再发下一条
                if i < len(threads):
                    print(f'   等待 60 秒...\n')
                    time.sleep(60)

            except Exception as e:
                if retry_count < max_retries:
                    print(f'⚠️  {i}/{len(threads)} 失败（重试 {retry_count+1}/{max_retries}）: {e}')
                    print(f'   等待 60 秒后重试...\n')
                    time.sleep(60)
                    retry_count += 1
                else:
                    print(f'❌ {i}/{len(threads)} 失败（已尝试 {max_retries+1} 次）: {e}')
                    last_tweet_id = None
                    success = True  # 放弃此条，继续下一条

    print(f'\n完成！成功发送 {success_count}/{len(threads)} 条推文')
    return success_count > 0

def main():
    if len(sys.argv) < 2:
        print('用法: python3 post_tweets_thread_v3.py <知识点名称>')
        sys.exit(1)

    knowledge_name = sys.argv[1]
    file_name = knowledge_name.replace(' ', '_') + '.md'
    file_path = Path(__file__).parent / file_name

    if not file_path.exists():
        print(f'❌ 文件不存在: {file_path}')
        sys.exit(1)

    threads = extract_sections(file_path)
    post_tweet_thread(threads)

if __name__ == '__main__':
    main()
