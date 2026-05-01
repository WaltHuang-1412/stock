#!/usr/bin/env python3
"""
個股追蹤系統 - Stock Tracker
用途：追蹤推薦股票7日表現，驗證準確率

執行時機：每日盤後14:30後
執行方式：python3 scripts/stock_tracker.py [--date YYYYMMDD]

最後更新：2026-01-22（跨平台修復）
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import requests

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 添加 scripts 目錄到路徑（P0 修復）
sys.path.insert(0, str(Path(__file__).parent))

from yahoo_finance_api import get_current_price

# 導入跨平台工具（P0 修復）
try:
    from utils import (
        get_tw_now,
        get_data_path,
        ensure_dir,
        read_json,
        write_json
    )
    USE_CROSS_PLATFORM = True
except ImportError:
    USE_CROSS_PLATFORM = False

from src.data_fetcher import DataFetcher


class StockTracker:
    def __init__(self, tracking_dir="data/tracking", reports_dir="data/tracking/reports"):
        """
        初始化追蹤器

        P0修復：使用跨平台路徑
        """
        if USE_CROSS_PLATFORM:
            self.tracking_dir = get_data_path('tracking')
            self.reports_dir = get_data_path('tracking', 'reports')
            ensure_dir(self.reports_dir)
        else:
            self.tracking_dir = Path(tracking_dir)
            self.reports_dir = Path(reports_dir)
            self.reports_dir.mkdir(parents=True, exist_ok=True)

    def get_all_tracking_files(self):
        """獲取所有追蹤中的JSON文件"""
        return list(self.tracking_dir.glob("tracking_*.json"))

    def load_tracking_data(self, file_path):
        """
        讀取追蹤數據

        P0修復：使用跨平台檔案讀取
        """
        if USE_CROSS_PLATFORM:
            return read_json(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    def save_tracking_data(self, file_path, data):
        """
        保存追蹤數據

        P0修復：使用跨平台檔案寫入
        """
        if USE_CROSS_PLATFORM:
            write_json(file_path, data)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def get_stock_price(self, stock_code):
        """獲取股票今日收盤價"""
        try:
            from yahoo_finance_api import get_stock_info
            info = get_stock_info(stock_code)

            if not info or info.get('current_price') is None:
                print(f"⚠️ {stock_code} 無法獲取股價數據")
                return None

            return {
                "close_price": round(info['current_price'], 2),
                "volume": info.get('volume', 0)
            }
        except Exception as e:
            print(f"❌ {stock_code} 獲取股價失敗: {e}")
            return None

    def get_institutional_data_safe(self, stock_code, date_str):
        """安全獲取法人數據（處理錯誤）"""
        try:
            # 使用 DataFetcher 獲取法人數據
            fetcher = DataFetcher()
            data = fetcher.fetch_institutional_data(stock_code)

            if data:
                return {
                    "investment_trust": data.get('investment_trust', 0),
                    "dealer": data.get('dealer', 0),
                    "foreign": data.get('foreign', 0),
                    "total": data.get('total', 0)
                }
            else:
                print(f"⚠️ {stock_code} {date_str} 法人數據不可用")
                return None
        except Exception as e:
            print(f"❌ {stock_code} {date_str} 獲取法人數據失敗: {e}")
            return None

    def update_tracking_record(self, recommendation, today_str):
        """更新單一推薦股票的追蹤記錄"""
        # 支援新舊兩種格式：stock_code (新) 或 symbol (舊)
        stock_code = recommendation.get('stock_code') or recommendation.get('symbol')
        stock_name = recommendation.get('stock_name') or recommendation.get('name')

        # 處理價格（可能是字串 "26.8-27.2" 或數字）
        recommend_price_raw = recommendation.get('recommend_price')
        if isinstance(recommend_price_raw, str):
            # 如果是範圍，取中間值
            if '-' in str(recommend_price_raw):
                prices = recommend_price_raw.split('-')
                recommend_price = float(prices[0])
            else:
                recommend_price = float(recommend_price_raw)
        else:
            recommend_price = float(recommend_price_raw) if recommend_price_raw else None

        # 處理目標價（可能是 "250" 或 "250（+8%）"）
        target_price_raw = recommendation.get('target_price', 0)
        try:
            if isinstance(target_price_raw, str):
                # 只取數字部分
                import re
                match = re.match(r'^[\d.]+', str(target_price_raw))
                target_price = float(match.group()) if match else 0
            else:
                target_price = float(target_price_raw)
        except (ValueError, AttributeError):
            target_price = 0

        # 處理停損價
        stop_loss_raw = recommendation.get('stop_loss', 0)
        try:
            if isinstance(stop_loss_raw, str):
                import re
                match = re.match(r'^[\d.]+', str(stop_loss_raw))
                stop_loss = float(match.group()) if match else 0
            else:
                stop_loss = float(stop_loss_raw)
        except (ValueError, AttributeError):
            stop_loss = 0

        # 檢查必要欄位
        if not stock_code:
            print(f"⚠️ 缺少股票代碼，跳過此筆記錄")
            return False
        if not recommend_price:
            print(f"⚠️ {stock_code} 缺少推薦價格，跳過此筆記錄")
            return False

        # 獲取今日股價
        price_data = self.get_stock_price(stock_code)
        if not price_data:
            return False

        close_price = price_data['close_price']
        volume = price_data['volume']

        # 計算漲跌幅
        gain_loss_pct = round(((close_price - recommend_price) / recommend_price) * 100, 2)

        # 獲取法人數據
        institutional = self.get_institutional_data_safe(stock_code, today_str)

        # 計算追蹤天數（支援不同的日期欄位名稱）
        recommend_date_str = recommendation.get('recommend_date') or recommendation.get('date')
        if not recommend_date_str:
            print(f"⚠️ {stock_code} 缺少推薦日期，跳過此筆記錄")
            return False

        # 處理不同的日期格式
        try:
            if '-' in recommend_date_str:
                recommend_date = datetime.strptime(recommend_date_str, "%Y-%m-%d")
            else:
                recommend_date = datetime.strptime(recommend_date_str, "%Y%m%d")
        except ValueError:
            print(f"⚠️ {stock_code} 日期格式錯誤：{recommend_date_str}")
            return False

        today_date = datetime.strptime(today_str, "%Y%m%d")
        days_tracked = (today_date - recommend_date).days

        # 建立今日更新記錄
        today_update = {
            "date": today_date.strftime("%Y-%m-%d"),
            "day": days_tracked,
            "close_price": close_price,
            "gain_loss_pct": gain_loss_pct,
            "volume": volume,
            "institutional_data": institutional,
            "notes": ""
        }

        # 判斷狀態
        if close_price >= target_price:
            today_update['notes'] = f"✅ 達目標價{target_price}元（+{gain_loss_pct}%）"
            recommendation['status'] = 'success'
        elif close_price <= stop_loss:
            today_update['notes'] = f"🚨 觸發停損{stop_loss}元（{gain_loss_pct}%）"
            recommendation['status'] = 'stop_loss'
        elif days_tracked >= recommendation.get('tracking_days', 7):  # 預設追蹤7天
            if gain_loss_pct >= 3:
                today_update['notes'] = f"✅ 7日追蹤完成、成功（+{gain_loss_pct}%）"
                recommendation['status'] = 'success'
            elif gain_loss_pct <= -3:
                today_update['notes'] = f"❌ 7日追蹤完成、失敗（{gain_loss_pct}%）"
                recommendation['status'] = 'failed'
            else:
                today_update['notes'] = f"⚠️ 7日追蹤完成、震盪（{gain_loss_pct}%）"
                recommendation['status'] = 'neutral'
        else:
            if institutional:
                total = institutional['total']
                if total > 1000:
                    today_update['notes'] = f"📈 法人買超+{total:,}張"
                elif total < -1000:
                    today_update['notes'] = f"📉 法人賣超{total:,}張"
                else:
                    today_update['notes'] = "⚠️ 法人買賣互抵"
            tracking_days = recommendation.get('tracking_days', 7)
            today_update['notes'] += f" 追蹤中 ({days_tracked}/{tracking_days}日)"

        # 加入每日更新列表（初始化如果不存在）
        if 'daily_updates' not in recommendation:
            recommendation['daily_updates'] = []
        recommendation['daily_updates'].append(today_update)

        # 輸出更新資訊
        print(f"✅ {stock_name}({stock_code}): {close_price}元 ({gain_loss_pct:+.2f}%) - {today_update['notes']}")

        return True

    def generate_7day_report(self, recommendation):
        """產生7日追蹤報告"""
        stock_code = recommendation['stock_code']
        stock_name = recommendation['stock_name']
        recommend_date = recommendation['recommend_date']

        # 計算最終結果
        daily_updates = recommendation['daily_updates']
        if not daily_updates:
            return

        last_update = daily_updates[-1]
        final_price = last_update['close_price']
        final_gain_loss = last_update['gain_loss_pct']
        recommend_price = recommendation['recommend_price']

        # 統計法人累計
        investment_total = sum([d['institutional_data']['investment_trust']
                                for d in daily_updates if d['institutional_data']], 0)
        foreign_total = sum([d['institutional_data']['foreign']
                            for d in daily_updates if d['institutional_data']], 0)

        # 產生報告
        report_date = datetime.strptime(recommend_date, "%Y-%m-%d")
        report_file = self.reports_dir / f"{recommend_date}_{stock_code}_7day_report.md"

        report = f"""# {stock_name}({stock_code}) 7日追蹤報告

**推薦日期**：{recommend_date}
**追蹤期間**：{recommend_date} 至 {last_update['date']}（{last_update['day']}日）
**報告產出**：{datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 📊 推薦資訊

- **推薦價**：{recommend_price}元
- **目標價**：{recommendation['target_price']}元（+{((recommendation['target_price']/recommend_price-1)*100):.1f}%）
- **停損價**：{recommendation['stop_loss']}元（-{((1-recommendation['stop_loss']/recommend_price)*100):.1f}%）
- **建議倉位**：{recommendation.get('position_size') or recommendation.get('position', '未指定')}
- **推薦理由**：{recommendation.get('recommend_reason') or recommendation.get('reason', '未指定')}

---

## 📈 追蹤結果

### 最終表現
- **7日收盤**：{final_price}元
- **漲跌幅**：**{final_gain_loss:+.2f}%**
- **狀態**：{'✅ 推薦成功' if recommendation['status'] == 'success' else '❌ 推薦失敗' if recommendation['status'] == 'failed' else '⚠️ 震盪中性'}

### 每日表現

| 日期 | 天數 | 收盤價 | 漲跌% | 投信 | 外資 | 三大法人 | 備註 |
|------|-----|--------|-------|------|------|---------|------|
"""

        for update in daily_updates:
            inst = update['institutional_data']
            if inst:
                inst_str = f"{inst['investment_trust']:+,d} | {inst['foreign']:+,d} | {inst['total']:+,d}"
            else:
                inst_str = "- | - | -"

            report += f"| {update['date']} | {update['day']} | {update['close_price']} | {update['gain_loss_pct']:+.2f}% | {inst_str} | {update['notes']} |\n"

        report += f"""
---

## 💰 法人態度

- **投信7日累計**：{investment_total:+,d}張
- **外資7日累計**：{foreign_total:+,d}張
- **判斷**：{'✅ 法人持續買超' if investment_total > 0 and foreign_total > 0 else '❌ 法人賣超或分歧'}

---

## 🎯 結論

"""

        if recommendation['status'] == 'success':
            report += f"""### ✅ 推薦成功（7日漲幅+{final_gain_loss:.2f}%）

**成功關鍵**：
- ✅ 法人持續買超（投信{investment_total:+,d}、外資{foreign_total:+,d}）
- ✅ 產業邏輯兌現
- ✅ 推薦價位佳（買在起漲點）

**策略有效**：投信+外資一致買超策略驗證成功
"""
        elif recommendation['status'] == 'failed':
            report += f"""### ❌ 推薦失敗（7日跌幅{final_gain_loss:.2f}%）

**失敗原因**：
- ❌ 法人棄守（投信{investment_total:+,d}、外資{foreign_total:+,d}）
- ❌ 產業邏輯未兌現
- ❌ {'外資0張陷阱' if any([d['institutional_data']['foreign'] == 0 for d in daily_updates if d['institutional_data']]) else '法人分歧'}

**教訓**：需加強篩選條件、避免類似錯誤
"""
        else:
            report += f"""### ⚠️ 震盪中性（7日漲跌{final_gain_loss:+.2f}%）

**原因分析**：
- ⚠️ 法人態度不明確（投信{investment_total:+,d}、外資{foreign_total:+,d}）
- ⚠️ 市場震盪、無明確趨勢
"""

        report += f"""
---

**免責聲明**：本報告僅供參考，不構成投資建議

**下次追蹤**：下一檔推薦股票
"""

        # 保存報告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"📄 已產生7日追蹤報告：{report_file}")

    def run(self, target_date=None):
        """
        執行追蹤更新

        P0修復：使用跨平台時區
        """
        # 確定追蹤日期
        if target_date:
            today = datetime.strptime(target_date, "%Y%m%d")
        else:
            # P0-2: 使用跨平台時區
            if USE_CROSS_PLATFORM:
                today = get_tw_now()
            else:
                today = datetime.now()

        today_str = today.strftime("%Y%m%d")
        today_display = today.strftime("%Y-%m-%d")

        print(f"📊 個股追蹤系統 - {today_display}")
        print("="*60)

        # 獲取所有追蹤文件
        tracking_files = self.get_all_tracking_files()

        if not tracking_files:
            print("ℹ️ 目前沒有追蹤中的股票")
            return

        print(f"找到 {len(tracking_files)} 個追蹤文件\n")

        # 逐一更新
        total_updated = 0
        total_completed = 0

        for file_path in tracking_files:
            print(f"\n處理文件：{file_path.name}")
            print("-"*60)

            data = self.load_tracking_data(file_path)

            # 支援不同格式：有些用 'recommendations'，有些直接存資料
            recommendations = data.get('recommendations', [])
            if not recommendations:
                print(f"ℹ️ 此檔案無推薦記錄或格式不同，跳過")
                continue

            for rec in recommendations:
                # 跳過已完成的（支援有或沒有 status 欄位的情況）
                status = rec.get('status', 'tracking')
                if status in ['success', 'failed', 'neutral', 'stop_loss']:
                    continue

                # 更新追蹤記錄
                if self.update_tracking_record(rec, today_str):
                    total_updated += 1

                    # 如果追蹤完成，產生報告
                    if rec.get('status') in ['success', 'failed', 'neutral', 'stop_loss']:
                        self.generate_7day_report(rec)
                        total_completed += 1

            # 更新metadata（如果存在）
            if 'metadata' not in data:
                data['metadata'] = {}
            # P0-2: 使用跨平台時區
            if USE_CROSS_PLATFORM:
                data['metadata']['updated_at'] = get_tw_now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                data['metadata']['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data['metadata']['tracking_active'] = len([r for r in recommendations if r.get('status', 'tracking') == 'tracking'])
            data['metadata']['tracking_completed'] = len([r for r in recommendations if r.get('status') in ['success', 'failed', 'neutral', 'stop_loss']])
            data['metadata']['success_count'] = len([r for r in recommendations if r.get('status') == 'success'])
            data['metadata']['stop_loss_count'] = len([r for r in recommendations if r.get('status') == 'stop_loss'])

            # 保存更新
            self.save_tracking_data(file_path, data)

        print("\n" + "="*60)
        print(f"✅ 追蹤更新完成")
        print(f"📊 本次更新：{total_updated} 檔")
        print(f"🎯 完成追蹤：{total_completed} 檔")


def main():
    """主程式"""
    import argparse

    parser = argparse.ArgumentParser(description='個股追蹤系統')
    parser.add_argument('--date', type=str, help='指定追蹤日期（格式：YYYYMMDD）')

    args = parser.parse_args()

    tracker = StockTracker()
    tracker.run(target_date=args.date)


if __name__ == '__main__':
    main()
