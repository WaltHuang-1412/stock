#!/usr/bin/env python3
"""
台股時事分析工具 v2.0
功能：
1. 查詢 MOPS 當日全市場重大訊息（不限特定股票）
2. 查詢近期法說會/股東會
3. 分析熱門題材
4. 整合財經新聞

用法：
  python3 scripts/fetch_tw_market_news.py           # 今日時事
  python3 scripts/fetch_tw_market_news.py --days 3  # 近3日時事
"""

import requests
import sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re

# 忽略 SSL 警告
import warnings
warnings.filterwarnings('ignore')

# 重點股票名稱對照（用於標註，不用於過濾）
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


def get_mops_all_announcements():
    """查詢 MOPS 當日全市場重大訊息"""
    announcements = []

    # MOPS 即時重大訊息（全市場）
    url = 'https://mops.twse.com.tw/mops/web/t05sr01_1'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
    }

    try:
        r = requests.get(url, headers=headers, timeout=20, verify=False)
        r.encoding = 'utf-8'

        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')

            # 找到重大訊息表格
            tables = soup.find_all('table', class_='hasBorder')

            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # 跳過表頭
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        try:
                            date = cols[0].get_text(strip=True)
                            time = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                            code = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                            name = cols[3].get_text(strip=True) if len(cols) > 3 else ''
                            subject = cols[4].get_text(strip=True) if len(cols) > 4 else ''

                            if code and subject:
                                # 清理股票代號（移除空白）
                                code = code.strip()

                                announcements.append({
                                    'date': date,
                                    'time': time,
                                    'stock_code': code,
                                    'stock_name': name,
                                    'subject': subject[:100],
                                    'is_major': code in STOCK_NAMES  # 標註是否為重點股票
                                })
                        except Exception:
                            continue

    except Exception as e:
        print(f"⚠️ MOPS 全市場查詢: {e}")

    return announcements


def get_mops_investor_conferences():
    """查詢 MOPS 法說會/業績發表會"""
    conferences = []

    today = datetime.now()

    # MOPS 法人說明會查詢
    url = 'https://mops.twse.com.tw/mops/web/t100sb02_1'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    try:
        # 查詢未來7天
        for i in range(7):
            check_date = today + timedelta(days=i)
            year = check_date.year - 1911  # 民國年
            month = check_date.month
            day = check_date.day

            data = {
                'encodeURIComponent': '1',
                'step': '1',
                'firstin': '1',
                'off': '1',
                'TYPEK': 'all',
                'year': str(year),
                'month': f'{month:02d}',
                'day': f'{day:02d}',
            }

            r = requests.post(url, headers=headers, data=data, timeout=10, verify=False)
            r.encoding = 'utf-8'

            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                tables = soup.find_all('table', class_='hasBorder')

                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:
                        cols = row.find_all('td')
                        if len(cols) >= 5:
                            try:
                                code = cols[0].get_text(strip=True)
                                name = cols[1].get_text(strip=True)
                                conf_type = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                                time = cols[3].get_text(strip=True)
                                location = cols[4].get_text(strip=True) if len(cols) > 4 else ''

                                if code and name:
                                    conferences.append({
                                        'date': check_date.strftime('%Y-%m-%d'),
                                        'stock_code': code.strip(),
                                        'stock_name': name,
                                        'type': conf_type,
                                        'time': time,
                                        'location': location,
                                        'is_major': code.strip() in STOCK_NAMES
                                    })
                            except Exception:
                                continue
    except Exception as e:
        print(f"⚠️ 法說會查詢: {e}")

    return conferences


def get_cnyes_news():
    """從鉅亨網查詢財經新聞"""
    news = []

    url = 'https://news.cnyes.com/api/v3/news/category/tw_stock'

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        params = {
            'page': 1,
            'limit': 20
        }

        r = requests.get(url, headers=headers, params=params, timeout=10)

        if r.status_code == 200:
            data = r.json()
            if 'items' in data and 'data' in data['items']:
                for item in data['items']['data'][:15]:
                    news.append({
                        'title': item.get('title', ''),
                        'date': datetime.fromtimestamp(item.get('publishAt', 0)).strftime('%Y-%m-%d %H:%M') if item.get('publishAt') else '',
                        'summary': item.get('summary', '')[:100]
                    })
    except Exception as e:
        print(f"⚠️ 鉅亨網查詢: {e}")

    return news


def get_upcoming_events():
    """查詢近期重要事件（手動維護）"""
    events = []

    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')

    # 重要事件日曆（可手動更新）
    important_events = [
        ('2026-01-20', '台積電法說會', '2330,2303,3711', '⚠️ 高'),
        ('2026-01-22', '聯發科法說會', '2454,3034', '⚠️ 高'),
        ('2026-01-29', 'Fed利率決議', '金融股', '⚠️ 高'),
        ('2026-02-05', '農曆春節前', '全市場', '📌 注意'),
    ]

    for date, event, stocks, impact in important_events:
        if date >= today_str:
            days_until = (datetime.strptime(date, '%Y-%m-%d') - today).days
            events.append({
                'date': date,
                'event': event,
                'stocks': stocks,
                'impact': impact,
                'days_until': days_until
            })

    return events[:5]


def analyze_news_keywords(news_list):
    """分析新聞關鍵字，找出熱門題材"""
    keywords = {}

    hot_topics = {
        'AI': ['AI', '人工智慧', 'GPU', '輝達', 'NVIDIA', 'ChatGPT'],
        '記憶體': ['記憶體', 'DRAM', 'HBM', 'NAND', '美光', 'Micron'],
        '半導體': ['半導體', '晶片', '晶圓', 'CoWoS', '先進封裝', '台積電'],
        '面板': ['面板', 'LCD', 'OLED', '顯示器', '群創', '友達'],
        '電動車': ['電動車', 'EV', '特斯拉', '電池', '充電'],
        '航運': ['航運', '運價', '貨櫃', 'BDI', '長榮', '陽明'],
        '金融': ['升息', '降息', 'Fed', '央行', '金融', '銀行'],
        '併購': ['併購', '收購', '合併', '股權'],
    }

    for news in news_list:
        title = news.get('title', '') + news.get('summary', '')
        for topic, kws in hot_topics.items():
            for kw in kws:
                if kw in title:
                    keywords[topic] = keywords.get(topic, 0) + 1
                    break

    sorted_topics = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
    return sorted_topics[:5]


def categorize_announcement(subject):
    """分類重大訊息"""
    if any(kw in subject for kw in ['法說會', '法人說明會', '業績發表', '業績說明']):
        return '📅 法說會', 1
    elif any(kw in subject for kw in ['合併', '收購', '併購', '股權轉讓', '公開收購']):
        return '🔗 併購', 2
    elif any(kw in subject for kw in ['訂單', '合約', '簽約', '接單', '得標']):
        return '📝 訂單', 3
    elif any(kw in subject for kw in ['擴產', '建廠', '投資', '產能', '新廠']):
        return '🏭 擴產', 4
    elif any(kw in subject for kw in ['庫藏股', '買回']):
        return '💰 庫藏股', 5
    elif any(kw in subject for kw in ['財報', '財務報告', '營收', '獲利', '盈餘']):
        return '📊 財報', 6
    elif any(kw in subject for kw in ['股利', '配息', '除權', '除息']):
        return '💵 股利', 7
    elif any(kw in subject for kw in ['董事', '監察人', '經理人', '總經理', '董事長']):
        return '👔 人事', 8
    elif any(kw in subject for kw in ['停工', '停產', '火災', '地震', '災害']):
        return '⚠️ 風險', 0  # 最高優先
    else:
        return '📌 其他', 9


def print_summary(announcements, conferences, cnyes_news, events, hot_topics):
    """輸出時事摘要"""
    today = datetime.now().strftime('%Y-%m-%d')
    weekday = ['一', '二', '三', '四', '五', '六', '日'][datetime.now().weekday()]
    time_now = datetime.now().strftime('%H:%M')

    print("\n" + "=" * 60)
    print(f"📢 台股時事掃描（{today} 週{weekday} {time_now}）")
    print("=" * 60)

    # 近期重要事件
    print("\n【⏰ 近期重要事件】")
    if events:
        for e in events:
            days = e['days_until']
            if days == 0:
                day_str = "⚠️ 今日"
            elif days == 1:
                day_str = "📍 明日"
            else:
                day_str = f"{days}日後"
            print(f"  {e['impact']} {e['date']} ({day_str}): {e['event']}")
            print(f"      影響：{e['stocks']}")
    else:
        print("  （近期無重大事件）")

    # 法說會（從 MOPS 查詢）
    print("\n【📅 近期法說會】")
    today_str = datetime.now().strftime('%Y-%m-%d')
    if conferences:
        today_conf = [c for c in conferences if c['date'] == today_str]
        future_conf = [c for c in conferences if c['date'] > today_str][:5]

        if today_conf:
            print("  ⚠️ 今日法說會：")
            for c in today_conf:
                major_mark = "⭐" if c.get('is_major') else ""
                print(f"    {major_mark} {c['stock_name']}({c['stock_code']}) {c['time']}")

        if future_conf:
            print("  📆 近期法說會：")
            for c in future_conf[:5]:
                major_mark = "⭐" if c.get('is_major') else ""
                print(f"    {major_mark} {c['date']} {c['stock_name']}({c['stock_code']})")
    else:
        print("  （近7日無法說會資料）")

    # 熱門題材
    print("\n【🔥 熱門題材】")
    if hot_topics:
        for topic, count in hot_topics:
            bar = "█" * min(count, 10)
            print(f"  • {topic}: {bar} ({count}則)")
    else:
        print("  （分析中...）")

    # 重大訊息（全市場，按類別分組）
    print("\n【📣 重大訊息】（全市場）")
    if announcements:
        # 按優先級分類
        categorized = {}
        for a in announcements:
            cat, priority = categorize_announcement(a['subject'])
            if cat not in categorized:
                categorized[cat] = {'items': [], 'priority': priority}
            categorized[cat]['items'].append(a)

        # 按優先級排序
        sorted_cats = sorted(categorized.items(), key=lambda x: x[1]['priority'])

        shown = 0
        for cat, data in sorted_cats:
            if shown >= 15:  # 最多顯示15筆
                break
            items = data['items'][:3]  # 每類最多3筆
            if items:
                print(f"\n  {cat}")
                for a in items:
                    major_mark = "⭐" if a.get('is_major') else ""
                    name = a.get('stock_name', '')[:4]
                    code = a.get('stock_code', '')
                    subject = a['subject'][:35]
                    print(f"    {major_mark} {name}({code}): {subject}...")
                    shown += 1
    else:
        print("  （今日暫無重大訊息或非交易日）")

    # 財經新聞
    print("\n【📰 財經新聞】")
    if cnyes_news:
        seen = set()
        count = 0
        for n in cnyes_news:
            title = n.get('title', '')[:45]
            if title and title not in seen and count < 8:
                seen.add(title)
                print(f"  • {title}...")
                count += 1
    else:
        print("  （新聞載入中...）")

    print("\n" + "=" * 60)
    print("✅ 掃描完成")
    print("=" * 60)

    # 圖例說明
    print("\n📌 說明：⭐ = 重點股票（市值前50）")

    return {
        'date': today,
        'events': events,
        'conferences': conferences,
        'hot_topics': hot_topics,
        'announcements': announcements,
        'news': cnyes_news[:10]
    }


def main():
    days = 1

    # 解析參數
    if len(sys.argv) > 1:
        if sys.argv[1] == '--days' and len(sys.argv) > 2:
            days = int(sys.argv[2])
        elif sys.argv[1] == '--help':
            print(__doc__)
            sys.exit(0)

    print("⏳ 正在掃描台股時事（全市場）...")

    # 查詢各資料源
    print("📡 查詢 MOPS 重大訊息（全市場）...")
    announcements = get_mops_all_announcements()
    print(f"   找到 {len(announcements)} 則訊息")

    print("📡 查詢 MOPS 法說會...")
    conferences = get_mops_investor_conferences()
    print(f"   找到 {len(conferences)} 場法說會")

    print("📡 查詢鉅亨網新聞...")
    cnyes_news = get_cnyes_news()

    print("📡 整理重要事件...")
    events = get_upcoming_events()

    print("📡 分析熱門題材...")
    hot_topics = analyze_news_keywords(cnyes_news)

    # 輸出摘要
    result = print_summary(announcements, conferences, cnyes_news, events, hot_topics)

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
