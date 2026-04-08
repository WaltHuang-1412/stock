#!/usr/bin/env python3
"""
盤中法人續買偵測器（12:30 執行）

邏輯：昨天法人在買的股票，今天盤中有沒有繼續被買？
用即時成交量異常 + 昨日法人方向交叉判斷

掃描對象（動態）：
1. 昨天 T86 法人連買 ≥2 天的股票
2. Module A 候選股（catalyst_preposition_scan.json）
3. 昨天 TOP30 買超股

篩選條件：
- 昨天法人淨買超 > 0
- 今天盤中量比 ≥ 1.2（成交量異常）
- 今天漲幅 < 3%（還沒反映）

輸出：data/YYYY-MM-DD/intraday_detector.json
供盤中 Track B 使用
"""

import sys
import os
import io
import json
import time
from pathlib import Path
from datetime import datetime
import requests

os.environ['PYTHONUTF8'] = '1'

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "data" / "cache"


# ===== T86 法人歷史 =====

def get_latest_t86_dates(n=10):
    """取得最近 N 個 T86 交易日"""
    files = sorted(CACHE_DIR.glob("twse_t86_*.json"))
    dates = [fp.stem.replace("twse_t86_", "") for fp in files]
    return dates[-n:]


def load_t86(date_str):
    fp = CACHE_DIR / f"twse_t86_{date_str}.json"
    if not fp.exists():
        return {}
    with open(fp, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_consecutive_buyers(t86_dates):
    """找出連續買超的股票 + 連買天數"""
    # 倒著看最近的交易日
    stock_streak = {}

    if not t86_dates:
        return {}

    # 從最新往回看
    for date in reversed(t86_dates):
        data = load_t86(date)
        for code, info in data.items():
            if not code.isdigit() or len(code) != 4 or code.startswith('00'):
                continue
            total = info.get('total', 0)

            if code not in stock_streak:
                if total > 0:
                    stock_streak[code] = {
                        'streak': 1,
                        'last_buy': total,
                        'cum_buy': total,
                        'latest_date': date,
                    }
                else:
                    stock_streak[code] = {'streak': 0}
            elif stock_streak[code]['streak'] > 0:
                if total > 0:
                    stock_streak[code]['streak'] += 1
                    stock_streak[code]['cum_buy'] += total
                else:
                    pass  # 已經斷了，不再往回看

    return {code: info for code, info in stock_streak.items() if info.get('streak', 0) >= 2}


def get_top_buyers(latest_date, top_n=30):
    """取得最新一天的 TOP N 買超"""
    data = load_t86(latest_date)
    items = [(code, info['total']) for code, info in data.items()
             if code.isdigit() and len(code) == 4 and not code.startswith('00') and info.get('total', 0) > 0]
    items.sort(key=lambda x: x[1], reverse=True)
    return {code: total for code, total in items[:top_n]}


# ===== Module A 候選 =====

def load_module_a_candidates(date):
    """讀取催化預埋掃描候選"""
    formatted = f"{date[:4]}-{date[4:6]}-{date[6:]}"
    fp = PROJECT_DIR / "data" / formatted / "catalyst_preposition_scan.json"
    if not fp.exists():
        # 嘗試昨天的
        for d in get_latest_t86_dates(5):
            fd = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            fp2 = PROJECT_DIR / "data" / fd / "catalyst_preposition_scan.json"
            if fp2.exists():
                fp = fp2
                break

    if not fp.exists():
        return []

    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)

    codes = []
    for level in ['L3', 'L2']:
        for stock in data.get(level, data.get(level.lower(), [])):
            code = stock.get('code', stock.get('stock_code', ''))
            if code:
                codes.append(code)
    return codes


# ===== TWSE 即時行情 =====

def fetch_realtime_batch(stock_codes):
    """從 TWSE 即時 API 批次取得行情"""
    results = {}

    # TWSE 每次最多查 20 檔
    batch_size = 20
    for i in range(0, len(stock_codes), batch_size):
        batch = stock_codes[i:i+batch_size]
        ex_ch = "|".join([f"tse_{code}.tw" for code in batch])
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={ex_ch}&json=1"

        try:
            r = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://mis.twse.com.tw/',
            }, timeout=10)
            data = r.json()

            for item in data.get('msgArray', []):
                code = item.get('c', '')
                if not code:
                    continue

                try:
                    # 即時價格
                    price = float(item.get('z', '0') or '0')
                    if price == 0:
                        price = float(item.get('l', '0') or '0')  # 用最低價
                    # 昨收
                    yesterday = float(item.get('y', '0') or '0')
                    # 成交量（股）
                    volume = int(item.get('v', '0') or '0')
                    # 股票名稱
                    name = item.get('n', code)

                    if yesterday > 0:
                        change_pct = (price - yesterday) / yesterday * 100
                    else:
                        change_pct = 0

                    results[code] = {
                        'code': code,
                        'name': name,
                        'price': price,
                        'yesterday': yesterday,
                        'change_pct': change_pct,
                        'volume': volume,  # 股
                    }
                except (ValueError, TypeError):
                    continue

        except Exception:
            pass

        if i + batch_size < len(stock_codes):
            time.sleep(0.3)

    return results


def fetch_avg_volume_batch(stock_codes):
    """用 Yahoo Finance 取得 20 日均量（回傳單位：張）"""
    avg_volumes = {}
    for code in stock_codes:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW"
            r = requests.get(url, params={"interval": "1d", "range": "30d"},
                           headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            data = r.json()
            volumes = [v for v in data['chart']['result'][0]['indicators']['quote'][0]['volume'] if v]
            if len(volumes) >= 5:
                # 排除今天（最後一天），取前 20 天均量
                # Yahoo volume 單位是「股」，轉成「張」（/1000）
                avg_vol_shares = sum(volumes[:-1]) / len(volumes[:-1])
                avg_volumes[code] = avg_vol_shares / 1000  # 股→張
        except Exception:
            pass
        time.sleep(0.2)

    return avg_volumes


# ===== 主程式 =====

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    today_compact = today.replace("-", "")

    print(f"盤中法人續買偵測器 — {today}")
    print()

    # Step 1: 收集掃描對象
    t86_dates = get_latest_t86_dates(10)
    if not t86_dates:
        print("無 T86 資料")
        return

    latest_date = t86_dates[-1]
    print(f"最新 T86: {latest_date}")

    # 連買股
    consecutive = find_consecutive_buyers(t86_dates)
    consecutive_codes = list(consecutive.keys())
    print(f"連買 ≥2 天: {len(consecutive_codes)} 檔")

    # TOP30
    top_buyers = get_top_buyers(latest_date, 30)
    top_codes = list(top_buyers.keys())
    print(f"昨日 TOP30: {len(top_codes)} 檔")

    # Module A
    module_a = load_module_a_candidates(latest_date)
    print(f"Module A 候選: {len(module_a)} 檔")

    # 合併去重
    all_codes = list(set(consecutive_codes + top_codes + module_a))
    print(f"合併後: {len(all_codes)} 檔")
    print()

    # Step 2: 取得即時行情
    print("取得即時行情...")
    realtime = fetch_realtime_batch(all_codes)
    print(f"取得 {len(realtime)} 檔即時資料")

    # Step 3: 取得均量（用來算量比）
    valid_codes = list(realtime.keys())
    print(f"取得均量...")
    avg_volumes = fetch_avg_volume_batch(valid_codes)
    print(f"取得 {len(avg_volumes)} 檔均量")
    print()

    # Step 4: 交叉篩選
    signals = []

    for code in valid_codes:
        rt = realtime[code]
        avg_vol = avg_volumes.get(code)
        consec = consecutive.get(code, {})
        in_top30 = code in top_buyers
        in_module_a = code in module_a

        if not avg_vol or avg_vol == 0:
            continue

        # TWSE 即時 volume 單位是「張」，avg_vol 也已轉為「張」
        volume_ratio = rt['volume'] / avg_vol

        # 篩選條件
        # 1. 昨天法人有在買（連買 or TOP30）
        has_institutional = consec.get('streak', 0) >= 2 or in_top30

        if not has_institutional:
            continue

        # 2. 今天量比 ≥ 1.2
        if volume_ratio < 1.2:
            continue

        # 3. 今天漲幅 < 5%（放寬：大盤強勢日 3% 很常見）
        if rt['change_pct'] >= 5:
            continue

        # 計算信號強度
        strength = 0
        reasons = []

        # 連買天數加分
        streak = consec.get('streak', 0)
        if streak >= 5:
            strength += 30
            reasons.append(f"連買{streak}天")
        elif streak >= 3:
            strength += 20
            reasons.append(f"連買{streak}天")
        elif streak >= 2:
            strength += 10
            reasons.append(f"連買{streak}天")

        # 量比加分
        if volume_ratio >= 2.5:
            strength += 30
            reasons.append(f"量比{volume_ratio:.1f}x(爆量)")
        elif volume_ratio >= 1.8:
            strength += 20
            reasons.append(f"量比{volume_ratio:.1f}x(放量)")
        elif volume_ratio >= 1.2:
            strength += 10
            reasons.append(f"量比{volume_ratio:.1f}x")

        # TOP30 加分
        if in_top30:
            strength += 15
            reasons.append("昨日TOP30")

        # Module A 加分
        if in_module_a:
            strength += 20
            reasons.append("Module A候選")

        # 漲幅越低越好（還沒反映）
        if rt['change_pct'] <= 0:
            strength += 15
            reasons.append(f"今日{rt['change_pct']:+.1f}%(未反映)")
        elif rt['change_pct'] <= 1:
            strength += 10
            reasons.append(f"今日{rt['change_pct']:+.1f}%(微漲)")

        # 累計買超量
        cum = consec.get('cum_buy', 0)
        if cum >= 20000:
            strength += 10
            reasons.append(f"累計{cum//1000}K")

        signals.append({
            'code': code,
            'name': rt['name'],
            'price': rt['price'],
            'change_pct': round(rt['change_pct'], 2),
            'volume_ratio': round(volume_ratio, 2),
            'streak': streak,
            'cum_buy': cum,
            'in_top30': in_top30,
            'in_module_a': in_module_a,
            'strength': strength,
            'reasons': reasons,
        })

    # 按強度排序
    signals.sort(key=lambda x: x['strength'], reverse=True)

    # Step 5: 輸出
    print("=" * 60)
    print(f"  盤中偵測結果 — {len(signals)} 檔可能法人續買")
    print("=" * 60)
    print()

    strong = [s for s in signals if s['strength'] >= 60]
    moderate = [s for s in signals if 40 <= s['strength'] < 60]
    weak = [s for s in signals if s['strength'] < 40]

    if strong:
        print("🔥 強訊號（≥60分）→ 建議進入 Track B 評分")
        for s in strong:
            reasons = " + ".join(s['reasons'])
            print(f"  {s['code']} {s['name']} {s['price']:.1f}({s['change_pct']:+.1f}%) 量比{s['volume_ratio']}x 強度{s['strength']} [{reasons}]")
        print()

    if moderate:
        print("⚠️ 中訊號（40-59分）→ 觀察")
        for s in moderate[:10]:
            reasons = " + ".join(s['reasons'])
            print(f"  {s['code']} {s['name']} {s['price']:.1f}({s['change_pct']:+.1f}%) 量比{s['volume_ratio']}x 強度{s['strength']} [{reasons}]")
        print()

    if not strong and not moderate:
        print("今日無明顯法人續買訊號")
        print()

    # 存 JSON
    out_dir = PROJECT_DIR / "data" / today
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "intraday_detector.json"
    output = {
        'date': today,
        'scan_time': datetime.now().strftime("%H:%M:%S"),
        'latest_t86': latest_date,
        'scanned': len(all_codes),
        'signals_count': len(signals),
        'strong': strong,
        'moderate': moderate[:10],
        'weak_count': len(weak),
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"已存: {out_path}")


if __name__ == "__main__":
    main()
