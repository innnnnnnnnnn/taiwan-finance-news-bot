import feedparser
import requests
import os
from datetime import datetime
import hashlib
from dotenv import load_dotenv
import time

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
KEYWORDS = [k.strip() for k in os.getenv('KEYWORDS', '台股,AI,半導體').split(',') if k.strip()]
INTERVAL = int(os.getenv('INTERVAL', 300))

RSS_FEEDS = [
    'https://ctee.com.tw/feed',                    # 工商時報
    'https://www.cna.com.tw/rss/topic/2',         # CNA 財經
    'https://feeds.feedburner.com/moneydj',       # MoneyDJ
    'https://ec.ltn.com.tw/rss/economy.xml',      # 自由時報 經濟
    'https://news.ltn.com.tw/rss/business.xml',   # 自由時報 財經
    'https://tw.stock.yahoo.com/rss',              # Yahoo 股市
    'https://technews.tw/feed/',                   # 科技新報 TechNews
    'https://udn.com/rssfeed/news/2/6644?ch=udn',  # 聯合新聞網 財經
    'https://tw.news.yahoo.com/rss/finance',       # Yahoo 奇摩新聞 財經
    'https://news.google.com/rss/search?q=台灣股市+OR+台股+OR+半導體+OR+財經&hl=zh-TW&gl=TW&ceid=TW:zh-Hant', # Google 新聞 (台股/財經)
]

SEEN_FILE = 'seen.txt'

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def save_seen(seen):
    with open(SEEN_FILE, 'w') as f:
        for s in list(seen)[-2000:]:
            f.write(s + '\n')

seen_hashes = load_seen()

def get_hash(title, link):
    return hashlib.md5(f'{title}{link}'.encode()).hexdigest()


def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print('⚠️ Telegram config missing')
        return False
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML', 'disable_web_page_preview': False}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except:
        return False


def fetch_news():
    news_list = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.title
                link = entry.get('link', '')
                summary = entry.get('summary', entry.get('description', ''))[:300]

                # 關鍵字過濾
                if KEYWORDS:
                    if not any(kw.lower() in (title + summary).lower() for kw in KEYWORDS):
                        continue

                news_hash = get_hash(title, link)
                if news_hash in seen_hashes:
                    continue
                seen_hashes.add(news_hash)

                news_list.append({
                    'title': title,
                    'link': link,
                    'summary': summary
                })
        except Exception as e:
            print(f'Error fetching {feed_url}: {e}')

    # 推送所有新新聞
    for news in news_list:
        message = f"<b>{news['title']}</b>\n\n{news['summary']}\n\n<a href='{news['link']}'>閱讀全文 →</a>"
        send_telegram(message)
        print(f'✅ 已推送: {news["title"][:50]}...')
    
    save_seen(seen_hashes)

if __name__ == '__main__':
    print(f'🚀 開始抓取台灣財經新聞 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    fetch_news()
    print('✅ 當次抓取與推播完成')