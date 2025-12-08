#!/usr/bin/env python3
"""
個人持股完整分析工具
結合即時價格、法人數據、時事分析、產業邏輯
使用方式：python3 scripts/my_holdings_analyzer.py
"""

import yfinance as yf
import yaml
import json
import requests
from datetime import datetime, timedelta
import subprocess
import os
import sys

class MyHoldingsAnalyzer:
    def __init__(self):
        self.holdings_file = "portfolio/my_holdings.yaml"
        self.current_prices = {}
        self.institutional_data = {}

    def load_holdings(self):
        """載入持股資料"""
        try:
            with open(self.holdings_file, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)

            # 只取有持股的股票（quantity > 0）
            active_holdings = []
            for holding in data['holdings']:
                if holding.get('quantity', 0) > 0:
                    active_holdings.append(holding)

            return active_holdings
        except Exception as e:
            print(f"❌ 讀取持股檔案失敗: {e}")
            return []

    def get_current_prices(self, holdings):
        """獲取即時股價"""
        print("📊 獲取即時股價...")

        for holding in holdings:
            stock_code = holding['symbol']
            try:
                ticker = yf.Ticker(f"{stock_code}.TW")
                info = ticker.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')

                if not current_price:
                    hist = ticker.history(period='1d')
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]

                if current_price:
                    self.current_prices[stock_code] = current_price
                    print(f"  ✅ {holding['name']}({stock_code}): {current_price:.2f}")
                else:
                    print(f"  ❌ {holding['name']}({stock_code}): 無法獲取價格")

            except Exception as e:
                print(f"  ❌ {holding['name']}({stock_code}): 獲取失敗 - {e}")

    def get_institutional_data(self, holdings):
        """獲取法人買賣超數據"""
        print("\n📈 查詢法人數據...")

        # 獲取最近交易日
        today = datetime.now()
        trade_date = self.get_latest_trade_date(today)
        date_str = trade_date.strftime('%Y%m%d')

        for holding in holdings:
            stock_code = holding['symbol']
            try:
                # 使用現有的 check_institutional.py 腳本
                result = subprocess.run([
                    'python3', 'scripts/check_institutional.py',
                    stock_code, date_str
                ], capture_output=True, text=True, cwd='.')

                if result.returncode == 0:
                    # 解析輸出
                    output_lines = result.stdout.strip().split('\n')
                    institutional_info = self.parse_institutional_output(output_lines)
                    self.institutional_data[stock_code] = institutional_info
                    print(f"  ✅ {holding['name']}({stock_code}): {institutional_info.get('total', 'N/A')}張")
                else:
                    print(f"  ❌ {holding['name']}({stock_code}): 查詢失敗")

            except Exception as e:
                print(f"  ❌ {holding['name']}({stock_code}): 查詢錯誤 - {e}")

    def parse_institutional_output(self, output_lines):
        """解析法人數據輸出"""
        data = {}
        for line in output_lines:
            if "外資:" in line:
                # 提取數字部分
                parts = line.replace('張', '').replace(',', '').split()
                for i, part in enumerate(parts):
                    if part == "外資:" and i + 1 < len(parts):
                        try:
                            data['foreign'] = int(parts[i + 1])
                        except:
                            data['foreign'] = 0
                        break
            elif "投信:" in line:
                parts = line.replace('張', '').replace(',', '').split()
                for i, part in enumerate(parts):
                    if part == "投信:" and i + 1 < len(parts):
                        try:
                            data['investment'] = int(parts[i + 1])
                        except:
                            data['investment'] = 0
                        break
            elif "三大法人:" in line:
                parts = line.replace('張', '').replace(',', '').split()
                for i, part in enumerate(parts):
                    if part == "三大法人:" and i + 1 < len(parts):
                        try:
                            data['total'] = int(parts[i + 1])
                        except:
                            data['total'] = 0
                        break
        return data

    def get_latest_trade_date(self, date):
        """獲取最近交易日（跳過週末）"""
        while date.weekday() > 4:  # 週六(5) 週日(6)
            date = date - timedelta(days=1)
        return date

    def analyze_performance(self, holdings):
        """分析持股表現"""
        print("\n" + "="*60)
        print("📊 您的持股完整分析報告")
        print("="*60)

        total_cost = 0
        total_value = 0
        analysis_results = []

        for holding in holdings:
            stock_code = holding['symbol']
            stock_name = holding['name']
            buy_price = holding['buy_price']
            quantity = holding.get('quantity', 1) * 1000  # 轉換為股數

            current_price = self.current_prices.get(stock_code, buy_price)
            institutional = self.institutional_data.get(stock_code, {})

            # 計算損益
            cost = buy_price * quantity
            value = current_price * quantity
            profit_loss = value - cost
            profit_pct = (profit_loss / cost) * 100 if cost > 0 else 0

            total_cost += cost
            total_value += value

            # 綜合評分
            score = self.calculate_health_score(profit_pct, institutional)
            rating = self.get_rating(score)
            suggestion = self.get_suggestion(score, profit_pct, institutional, stock_name)

            analysis_results.append({
                'name': stock_name,
                'code': stock_code,
                'buy_price': buy_price,
                'current_price': current_price,
                'profit_pct': profit_pct,
                'profit_loss': profit_loss,
                'institutional': institutional,
                'score': score,
                'rating': rating,
                'suggestion': suggestion
            })

        # 排序：問題股票優先顯示
        analysis_results.sort(key=lambda x: x['score'])

        # 顯示分析結果
        self.display_analysis_results(analysis_results, total_cost, total_value)

        return analysis_results

    def calculate_health_score(self, profit_pct, institutional):
        """計算健康度評分（100分制）"""
        score = 70  # 基礎分數

        # 報酬率評分（40分）
        if profit_pct > 15:
            score += 20  # 大賺
        elif profit_pct > 5:
            score += 10  # 小賺
        elif profit_pct > -5:
            score += 0   # 平盤
        elif profit_pct > -10:
            score -= 20  # 小虧
        else:
            score -= 40  # 大虧

        # 法人態度評分（30分）
        total_institutional = institutional.get('total', 0)
        if total_institutional > 5000:
            score += 30  # 大買超
        elif total_institutional > 1000:
            score += 15  # 小買超
        elif total_institutional > -1000:
            score += 0   # 平盤
        elif total_institutional > -5000:
            score -= 15  # 小賣超
        else:
            score -= 30  # 大賣超

        return max(0, min(100, score))

    def get_rating(self, score):
        """根據評分給出等級"""
        if score >= 85:
            return "🟢 優秀"
        elif score >= 70:
            return "🟢 良好"
        elif score >= 55:
            return "🟡 普通"
        elif score >= 40:
            return "🟡 警戒"
        else:
            return "🔴 危險"

    def get_suggestion(self, score, profit_pct, institutional, stock_name):
        """給出操作建議"""
        total_institutional = institutional.get('total', 0)

        if score <= 40:
            if profit_pct < -8:
                return "🔴 建議停損出場"
            else:
                return "🔴 建議減碼觀察"
        elif score <= 55:
            if total_institutional < -1000:
                return "🟡 法人棄守，警戒觀察"
            else:
                return "🟡 短期持有，注意法人動向"
        elif score >= 85:
            if total_institutional > 10000:
                return "🟢 法人大買超，建議加碼"
            elif profit_pct > 15:
                return "🟢 獲利豐厚，可考慮部分獲利了結"
            else:
                return "🟢 表現優秀，建議續抱"
        else:
            return "🟢 續抱觀察"

    def display_analysis_results(self, results, total_cost, total_value):
        """顯示分析結果"""
        print()

        # 個股分析
        for result in results:
            print(f"📈 {result['name']}({result['code']}) - 評分：{result['score']}/100 {result['rating']}")
            print(f"├─ 買入價：{result['buy_price']:.2f} → 現價：{result['current_price']:.2f}")

            profit_emoji = "🟢" if result['profit_pct'] > 0 else "🔴"
            print(f"├─ 損益：{profit_emoji} {result['profit_pct']:+.2f}% ({result['profit_loss']:+,.0f}元)")

            institutional = result['institutional']
            if institutional:
                total_inst = institutional.get('total', 0)
                inst_emoji = "🟢" if total_inst > 0 else "🔴" if total_inst < 0 else "➖"
                print(f"├─ 法人：{inst_emoji} {total_inst:+,}張 (外資{institutional.get('foreign', 0):+,} 投信{institutional.get('investment', 0):+,})")

            print(f"└─ 建議：{result['suggestion']}")
            print()

        # 總結
        total_profit = total_value - total_cost
        total_profit_pct = (total_profit / total_cost) * 100 if total_cost > 0 else 0
        profit_emoji = "🟢" if total_profit > 0 else "🔴"

        print("📋 投資組合總結")
        print("-" * 40)
        print(f"總成本：{total_cost:,.0f} 元")
        print(f"總市值：{total_value:,.0f} 元")
        print(f"總損益：{profit_emoji} {total_profit:+,.0f} 元 ({total_profit_pct:+.2f}%)")

        # 操作建議統計
        high_risk = len([r for r in results if r['score'] <= 40])
        high_potential = len([r for r in results if r['score'] >= 85])

        print(f"\n🎯 操作統計：")
        print(f"高風險股票：{high_risk} 檔 (建議處理)")
        print(f"優質股票：{high_potential} 檔 (可考慮加碼)")

    def run_analysis(self):
        """執行完整分析"""
        print("🚀 開始分析您的持股...")

        # 載入持股
        holdings = self.load_holdings()
        if not holdings:
            print("❌ 沒有找到持股資料")
            return

        print(f"📂 找到 {len(holdings)} 檔持股")

        # 獲取數據
        self.get_current_prices(holdings)
        self.get_institutional_data(holdings)

        # 分析結果
        results = self.analyze_performance(holdings)

        print(f"\n✅ 分析完成！ 分析時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        analyzer = MyHoldingsAnalyzer()
        analyzer.run_analysis()
    except KeyboardInterrupt:
        print("\n\n❌ 使用者中斷分析")
    except Exception as e:
        print(f"\n❌ 分析過程出錯：{e}")