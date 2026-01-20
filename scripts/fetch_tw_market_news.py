#!/usr/bin/env python3
"""
台股時事分析工具 v3.0
整合多來源動態獲取台股資訊：
1. 證交所新聞 API - 官方公告
2. 證交所公告 API - 重大訊息
3. 鉅亨網新聞 API - 財經新聞 + 關鍵字
4. 經濟日報 RSS - 補充新聞

所有資料皆從即時來源動態獲取，無硬編碼

用法：
  python3 scripts/fetch_tw_market_news.py
"""

import requests
import sys
from datetime import datetime
from bs4 import BeautifulSoup
import json
import re
import xml.etree.ElementTree as ET

# 忽略 SSL 警告
import warnings
warnings.filterwarnings('ignore')

# 重點股票名稱對照（用於標註）
STOCK_NAMES = {
    # 半導體
    '2330': '台積電', '2303': '聯電', '2454': '聯發科', '3711': '日月光投控',
    '2379': '瑞昱', '3034': '聯詠', '6770': '力積電', '2408': '南亞科',
    '2344': '華邦電', '2337': '旺宏',
    # 電子
    '2317': '鴻海', '2382': '廣達', '3231': '緯創', '2357': '華碩',
    '3037': '欣興', '3189': '景碩', '8046': '南電', '6239': '力成',
    # 金融
    '2881': '富邦金', '2882': '國泰金', '2883': '凱基金', '2884': '玉山金',
    '2885': '元大金', '2886': '兆豐金', '2887': '台新金', '2891': '中信金',
    '2890': '永豐金', '2892': '第一金',
    # 傳產
    '1301': '台塑', '1303': '南亞', '1326': '台化', '2002': '中鋼',
    '2603': '長榮', '2609': '陽明', '2615': '萬海',
    # 其他
    '3481': '群創', '2409': '友達', '8150': '南茂'
}


def get_twse_news():
    """從證交所獲取官方新聞"""
    news = []
    url = 'https://www.twse.com.tw/rwd/zh/news/newsList?limit=15'

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('stat') == 'ok' and 'data' in data:
                for item in data['data'][:10]:
                    if len(item) >= 3:
                        news.append({
                            'title': item[1][:80] if len(item) > 1 else '',
                            'date': item[2] if len(item) > 2 else '',
                            'source': '證交所',
                            'type': 'official'
                        })
    except Exception as e:
        print(f"  ⚠️ 證交所新聞: {e}")

    return news


def get_twse_announcements():
    """從證交所獲取公告"""
    announcements = []
    url = 'https://www.twse.com.tw/rwd/zh/announcement/announcement?limit=10'

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('stat') == 'ok' and 'data' in data:
                for item in data['data'][:8]:
                    if len(item) >= 4:
                        announcements.append({
                            'date': item[1] if len(item) > 1 else '',
                            'doc_no': item[2] if len(item) > 2 else '',
                            'subject': item[3][:100] if len(item) > 3 else '',
                            'source': '證交所公告'
                        })
    except Exception as e:
        print(f"  ⚠️ 證交所公告: {e}")

    return announcements


def get_cnyes_news():
    """從鉅亨網獲取財經新聞"""
    news = []
    url = 'https://news.cnyes.com/api/v3/news/category/tw_stock'

    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        params = {'page': 1, 'limit': 20}

        r = requests.get(url, headers=headers, params=params, timeout=10)

        if r.status_code == 200:
            data = r.json()
            if 'items' in data and 'data' in data['items']:
                for item in data['items']['data'][:15]:
                    publish_time = item.get('publishAt', 0)
                    date_str = datetime.fromtimestamp(publish_time).strftime('%Y-%m-%d %H:%M') if publish_time else ''

                    news.append({
                        'title': item.get('title', ''),
                        'date': date_str,
                        'summary': item.get('summary', '')[:100],
                        'keywords': item.get('keyword', []),
                        'source': '鉅亨網'
                    })
    except Exception as e:
        print(f"  ⚠️ 鉅亨網新聞: {e}")

    return news


def get_udn_rss():
    """從經濟日報 RSS 獲取新聞"""
    news = []
    url = 'https://money.udn.com/rssfeed/news/1001/5590'

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            root = ET.fromstring(r.content)

            for item in root.findall('.//item')[:10]:
                title = item.find('title')
                pub_date = item.find('pubDate')

                if title is not None:
                    news.append({
                        'title': title.text[:80] if title.text else '',
                        'date': pub_date.text[:25] if pub_date is not None and pub_date.text else '',
                        'source': '經濟日報'
                    })
    except Exception as e:
        print(f"  ⚠️ 經濟日報 RSS: {e}")

    return news


def detect_conferences(all_news):
    """從新聞中偵測法說會資訊"""
    conferences = []
    conf_keywords = ['法說', '法人說明', '業績發表', '業績說明會']

    seen = set()
    for news in all_news:
        title = news.get('title', '')

        if any(kw in title for kw in conf_keywords):
            # 嘗試提取股票名稱
            for code, name in STOCK_NAMES.items():
                if name in title and code not in seen:
                    seen.add(code)
                    conferences.append({
                        'stock_code': code,
                        'stock_name': name,
                        'title': title[:60],
                        'date': news.get('date', ''),
                        'source': news.get('source', '')
                    })
                    break

    return conferences


def detect_events(all_news):
    """從新聞中偵測重要事件"""
    events = []

    event_keywords = {
        'Fed': ('Fed利率決議', '金融股', '⚠️ 高'),
        '升息': ('央行升息', '金融股', '⚠️ 高'),
        '降息': ('央行降息', '金融股', '⚠️ 高'),
        'CPI': ('CPI公布', '全市場', '📌 注意'),
        '非農': ('非農就業數據', '全市場', '📌 注意'),
        '財報': ('財報季', '全市場', '📌 注意'),
        '除息': ('除權息旺季', '高息股', '📌 注意'),
    }

    detected = set()
    for news in all_news:
        title = news.get('title', '') + news.get('summary', '')

        for keyword, (event_name, stocks, impact) in event_keywords.items():
            if keyword in title and event_name not in detected:
                detected.add(event_name)
                events.append({
                    'event': event_name,
                    'stocks': stocks,
                    'impact': impact,
                    'source_title': news.get('title', '')[:40],
                    'date': news.get('date', '')
                })

    return events[:5]


def analyze_hot_topics(all_news):
    """分析熱門題材"""
    keywords = {}

    hot_topics = {
        'AI': ['AI', '人工智慧', 'GPU', '輝達', 'NVIDIA', 'ChatGPT', 'Blackwell'],
        '記憶體': ['記憶體', 'DRAM', 'HBM', 'NAND', '美光', 'Micron'],
        '半導體': ['半導體', '晶片', '晶圓', 'CoWoS', '先進封裝', '台積電'],
        '面板': ['面板', 'LCD', 'OLED', '顯示器', '群創', '友達'],
        '電動車': ['電動車', 'EV', '特斯拉', '電池', '充電'],
        '航運': ['航運', '運價', '貨櫃', 'BDI', '長榮', '陽明'],
        '金融': ['升息', '降息', 'Fed', '央行', '金融', '銀行', '壽險'],
        '併購': ['併購', '收購', '合併', '股權'],
        'ETF': ['ETF', '成分股', '調整', '納入'],
    }

    for news in all_news:
        text = news.get('title', '') + news.get('summary', '')
        # 也使用鉅亨網提供的關鍵字
        if news.get('keywords'):
            text += ' '.join(news.get('keywords', []))

        for topic, kws in hot_topics.items():
            for kw in kws:
                if kw in text:
                    keywords[topic] = keywords.get(topic, 0) + 1
                    break

    return sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:6]


def print_summary(twse_news, twse_announcements, cnyes_news, udn_news, conferences, events, hot_topics):
    """輸出時事摘要"""
    today = datetime.now().strftime('%Y-%m-%d')
    weekday = ['一', '二', '三', '四', '五', '六', '日'][datetime.now().weekday()]
    time_now = datetime.now().strftime('%H:%M')

    print("\n" + "=" * 60)
    print(f"📢 台股時事掃描 v3.0（{today} 週{weekday} {time_now}）")
    print("=" * 60)

    # 熱門題材
    print("\n【🔥 熱門題材】")
    if hot_topics:
        for topic, count in hot_topics:
            bar = "█" * min(count, 10)
            print(f"  • {topic}: {bar} ({count}則)")
    else:
        print("  （分析中...）")

    # 偵測到的重要事件
    print("\n【⏰ 偵測到的事件】")
    if events:
        for e in events:
            print(f"  {e['impact']} {e['event']} - 影響：{e['stocks']}")
            print(f"      來源：{e['source_title']}...")
    else:
        print("  （今日新聞未偵測到重大事件）")

    # 偵測到的法說會
    print("\n【📅 偵測到的法說會】")
    if conferences:
        for c in conferences:
            print(f"  ⭐ {c['stock_name']}({c['stock_code']})")
            print(f"      {c['title'][:50]}...")
    else:
        print("  （今日新聞未提及法說會）")

    # 證交所官方公告
    print("\n【📣 證交所公告】")
    if twse_announcements:
        for a in twse_announcements[:5]:
            print(f"  • {a['subject'][:55]}...")
    else:
        print("  （無最新公告）")

    # 證交所新聞
    print("\n【📰 證交所新聞】")
    if twse_news:
        for n in twse_news[:5]:
            print(f"  • {n['title'][:55]}...")
    else:
        print("  （無最新新聞）")

    # 財經新聞（鉅亨網 + 經濟日報）
    print("\n【📰 財經新聞】")
    all_financial_news = cnyes_news + udn_news
    if all_financial_news:
        seen = set()
        count = 0
        for n in all_financial_news:
            title = n.get('title', '')[:50]
            if title and title not in seen and count < 10:
                seen.add(title)
                source = n.get('source', '')
                print(f"  [{source}] {title}...")
                count += 1
    else:
        print("  （載入中...）")

    print("\n" + "=" * 60)
    print("✅ 掃描完成（資料來源：證交所、鉅亨網、經濟日報）")
    print("=" * 60)

    return {
        'date': today,
        'hot_topics': hot_topics,
        'events': events,
        'conferences': conferences,
        'announcements': twse_announcements,
        'twse_news': twse_news,
        'news': cnyes_news[:10]
    }


def main():
    print("⏳ 正在掃描台股時事...")

    # 查詢各來源
    print("📡 查詢證交所新聞...")
    twse_news = get_twse_news()
    print(f"   找到 {len(twse_news)} 則")

    print("📡 查詢證交所公告...")
    twse_announcements = get_twse_announcements()
    print(f"   找到 {len(twse_announcements)} 則")

    print("📡 查詢鉅亨網新聞...")
    cnyes_news = get_cnyes_news()
    print(f"   找到 {len(cnyes_news)} 則")

    print("📡 查詢經濟日報...")
    udn_news = get_udn_rss()
    print(f"   找到 {len(udn_news)} 則")

    # 整合所有新聞進行分析
    all_news = twse_news + cnyes_news + udn_news

    print("📡 分析熱門題材...")
    hot_topics = analyze_hot_topics(all_news)

    print("📡 偵測法說會...")
    conferences = detect_conferences(all_news)
    print(f"   偵測到 {len(conferences)} 場")

    print("📡 偵測重要事件...")
    events = detect_events(all_news)
    print(f"   偵測到 {len(events)} 個")

    # 輸出摘要
    result = print_summary(twse_news, twse_announcements, cnyes_news, udn_news,
                          conferences, events, hot_topics)

    # 儲存結果
    today = datetime.now().strftime('%Y-%m-%d')
    output_dir = f'data/{today}'

    try:
        import os
        os.makedirs(output_dir, exist_ok=True)

        output_file = f'{output_dir}/tw_market_news.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾 已儲存至 {output_file}")
    except Exception as e:
        print(f"\n⚠️ 儲存失敗: {e}")


if __name__ == '__main__':
    main()
