"""
個人持股分析模組
分析持股現況並提供離場建議
"""

import yaml
from datetime import datetime, timedelta
from data_fetcher import DataFetcher
from analyzer import StockAnalyzer

class PortfolioAnalyzer:
    def __init__(self, holdings_file="../portfolio/my_holdings.yaml"):
        self.holdings_file = holdings_file
        self.data_fetcher = DataFetcher()
        self.analyzer = StockAnalyzer()
        
    def load_holdings(self):
        """載入持股資料"""
        try:
            with open(self.holdings_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('holdings', []), data.get('strategy', {})
        except FileNotFoundError:
            print(f"❌ 找不到持股檔案: {self.holdings_file}")
            print("請先編輯 my_holdings.yaml 檔案，填入你的持股資訊")
            return [], {}
        except Exception as e:
            print(f"❌ 讀取持股檔案失敗: {e}")
            return [], {}
    
    def analyze_portfolio(self):
        """分析整個投資組合"""
        holdings, strategy = self.load_holdings()
        
        if not holdings:
            return "❌ 沒有持股資料"
        
        print("📊 正在分析你的持股...")
        
        results = []
        total_cost = 0
        total_current_value = 0
        
        for holding in holdings:
            symbol = holding.get('symbol')
            name = holding.get('name', symbol)
            buy_price = float(holding.get('buy_price', 0))
            quantity = int(holding.get('quantity', 0))
            buy_date = holding.get('buy_date', '')
            
            # 獲取當前股價和法人數據
            current_data = self.data_fetcher.fetch_all_data(symbol, 'taiwan')
            institutional_data = current_data.get('institutional_data', {})
            stock_data = current_data.get('stock_data', {})
            
            current_price = self._extract_current_price(stock_data)
            
            # 計算損益
            cost = buy_price * quantity * 1000  # 轉換為元
            current_value = current_price * quantity * 1000 if current_price else 0
            profit_loss = current_value - cost
            profit_loss_percent = (profit_loss / cost * 100) if cost > 0 else 0
            
            total_cost += cost
            total_current_value += current_value
            
            # 離場建議
            exit_advice = self._generate_exit_advice(
                symbol, current_price, buy_price, profit_loss_percent, 
                institutional_data, strategy
            )
            
            result = {
                'symbol': symbol,
                'name': name,
                'buy_price': buy_price,
                'current_price': current_price,
                'quantity': quantity,
                'cost': cost,
                'current_value': current_value,
                'profit_loss': profit_loss,
                'profit_loss_percent': profit_loss_percent,
                'buy_date': buy_date,
                'exit_advice': exit_advice,
                'institutional_data': institutional_data
            }
            
            results.append(result)
        
        # 整體投資組合分析
        total_profit_loss = total_current_value - total_cost
        total_profit_loss_percent = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
        
        return self._format_portfolio_report(results, total_cost, total_current_value, 
                                           total_profit_loss, total_profit_loss_percent)
    
    def _extract_current_price(self, stock_data):
        """提取當前股價"""
        if not stock_data:
            return None
            
        price = stock_data.get('current_price')
        if price and price != 'N/A':
            try:
                return float(price)
            except (ValueError, TypeError):
                pass
        return None
    
    def _generate_exit_advice(self, symbol, current_price, buy_price, profit_percent, 
                            institutional_data, strategy):
        """生成離場建議"""
        if not current_price or not buy_price:
            return "❌ 無法獲取價格資訊"
        
        advice = []
        
        # 停損停利檢查
        stop_loss = strategy.get('stop_loss_percent', -10)
        take_profit = strategy.get('take_profit_percent', 20)
        
        if profit_percent <= stop_loss:
            advice.append("🚨 建議停損離場")
        elif profit_percent >= take_profit:
            advice.append("💰 可考慮停利離場")
        
        # 法人動向分析
        if institutional_data:
            foreign_net = institutional_data.get('foreign_net', 0)
            trust_net = institutional_data.get('investment_trust_net', 0)
            
            if isinstance(foreign_net, (int, float)) and foreign_net < -1000:
                advice.append("⚠️ 外資大幅賣超，建議觀望")
            elif isinstance(foreign_net, (int, float)) and foreign_net > 1000:
                advice.append("✅ 外資持續買超，可續抱")
            
            if isinstance(trust_net, (int, float)) and trust_net < -500:
                advice.append("⚠️ 投信轉為賣超")
        
        # 價格位置分析
        if profit_percent > 10:
            advice.append("📈 已有不錯獲利，可部分獲利了結")
        elif -5 <= profit_percent <= 5:
            advice.append("📊 持平區間，觀察後續走勢")
        
        return advice if advice else ["📊 目前可持續觀察"]
    
    def _format_portfolio_report(self, results, total_cost, total_current_value, 
                                total_profit_loss, total_profit_loss_percent):
        """格式化投資組合報告"""
        report = "=" * 60 + "\n"
        report += "📊 **個人持股分析報告**\n"
        report += "=" * 60 + "\n\n"
        
        # 整體概況
        report += f"💰 **投資組合概況**\n"
        report += f"總成本: {total_cost:,.0f} 元\n"
        report += f"目前市值: {total_current_value:,.0f} 元\n"
        report += f"總損益: {total_profit_loss:+,.0f} 元 ({total_profit_loss_percent:+.1f}%)\n\n"
        
        # 個股分析
        report += "📈 **個股分析**\n\n"
        
        for result in results:
            symbol = result['symbol']
            name = result['name']
            buy_price = result['buy_price']
            current_price = result['current_price']
            quantity = result['quantity']
            profit_loss = result['profit_loss']
            profit_loss_percent = result['profit_loss_percent']
            exit_advice = result['exit_advice']
            
            report += f"**{name} ({symbol})**\n"
            current_price_str = f"{current_price:.1f}" if current_price else "N/A"
            report += f"買入價: {buy_price:.1f} → 現價: {current_price_str}\n"
            report += f"持有: {quantity:,} 張\n"
            report += f"損益: {profit_loss:+,.0f} 元 ({profit_loss_percent:+.1f}%)\n"
            
            report += "**離場建議**:\n"
            for advice in exit_advice:
                report += f"• {advice}\n"
            
            report += "\n"
        
        report += "=" * 60 + "\n"
        report += "⚠️ **免責聲明**: 以上分析僅供參考，投資決策請自行判斷\n"
        
        return report

def main():
    analyzer = PortfolioAnalyzer()
    report = analyzer.analyze_portfolio()
    print(report)

if __name__ == "__main__":
    main()