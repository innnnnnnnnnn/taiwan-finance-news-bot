import feedparser
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import hashlib

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# 台灣財經新聞 RSS 來源
RSS_FEEDS = [
    'https://ctee.com.tw/feed',  # 工商時報
    'https://feeds.feedburner.com/rsscna/engnews',  # Focus Taiwan Business
    'https://www.cna.com.tw/topic/newstopic/2.aspx',  # CNA 財經
    # 可再新增更多
]

seen_hashes = set()

def get_hash(title, link):
    return hashlib.md5(f'{title}{link}'.encode()).hexdigest()

def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print('Telegram config missing')
        return
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    requests.post(url, json=payload)

def fetch_news():
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:  # 每來源取最新5則
            title = entry.title
            link = entry.link
            summary = entry.get('summary', '')[:200]
            pub_time = entry.get('published_parsed') or entry.get('updated_parsed')
            
            news_hash = get_hash(title, link)
            if news_hash in seen_hashes:
                continue
            seen_hashes.add(news_hash)
            
            message = f'<b>{title}</b>\n\n{summary}\n\n<a href="{link}">閱讀全文</a>'
            send_telegram(message)
            print(f'推送: {title}')

if __name__ == '__main__':
    fetch_news()