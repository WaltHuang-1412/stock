import openai
import yaml
from datetime import datetime
import json
import logging
from typing import Dict, List, Any

class StockAnalyzer:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 設置OpenAI API
        openai.api_key = self.config['api']['openai_api_key']
        
        # 設置日誌
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def analyze_data(self, query_info: Dict, data: Dict) -> str:
        """主要分析函數"""
        try:
            analysis_types = query_info.get('analysis_type', [])
            
            # 根據分析類型選擇分析方法
            analysis_results = []
            
            if 'institutional' in analysis_types:
                institutional_analysis = self._analyze_institutional_data(query_info, data)
                if institutional_analysis:
                    analysis_results.append(institutional_analysis)
            
            if 'news' in analysis_types:
                news_analysis = self._analyze_news_data(query_info, data)
                if news_analysis:
                    analysis_results.append(news_analysis)
            
            if 'technical' in analysis_types:
                technical_analysis = self._analyze_technical_data(query_info, data)
                if technical_analysis:
                    analysis_results.append(technical_analysis)
            
            if 'recommendation' in analysis_types:
                recommendation_analysis = self._analyze_recommendation_data(query_info, data)
                if recommendation_analysis:
                    analysis_results.append(recommendation_analysis)
            
            if 'general' in analysis_types or (not analysis_results and 'recommendation' not in analysis_types):
                general_analysis = self._analyze_general_data(query_info, data)
                if general_analysis:
                    analysis_results.append(general_analysis)
            
            # 使用AI整合所有分析結果
            final_analysis = self._generate_comprehensive_analysis(query_info, analysis_results, data)
            
            return final_analysis
            
        except Exception as e:
            self.logger.error(f"分析數據時發生錯誤: {e}")
            return f"分析過程中發生錯誤: {e}"
    
    def _analyze_institutional_data(self, query_info: Dict, data: Dict) -> str:
        """分析法人數據"""
        try:
            institutional_data = data.get('institutional_data')
            if not institutional_data:
                return "❌ 無法獲取法人數據"
            
            symbol = query_info.get('stock_symbol', 'N/A')
            stock_name = query_info.get('stock_name', '')
            
            analysis = f"📊 **法人分析 ({symbol} {stock_name})**\n\n"
            
            # 分析外資動向
            foreign_net = institutional_data.get('foreign_net', 0)
            if isinstance(foreign_net, (int, float)) and foreign_net != 0:
                if foreign_net > 0:
                    analysis += f"🔵 **外資**: 買超 {foreign_net:,.0f} 張\n"
                else:
                    analysis += f"🔴 **外資**: 賣超 {abs(foreign_net):,.0f} 張\n"
            else:
                analysis += "🔵 **外資**: 中性\n"
            
            # 分析投信動向
            trust_net = institutional_data.get('investment_trust_net', 0)
            if isinstance(trust_net, (int, float)) and trust_net != 0:
                if trust_net > 0:
                    analysis += f"🔵 **投信**: 買超 {trust_net:,.0f} 張\n"
                else:
                    analysis += f"🔴 **投信**: 賣超 {abs(trust_net):,.0f} 張\n"
            else:
                analysis += "🔵 **投信**: 中性\n"
            
            # 分析自營商動向
            dealer_net = institutional_data.get('dealer_net', 0)
            if isinstance(dealer_net, (int, float)) and dealer_net != 0:
                if dealer_net > 0:
                    analysis += f"🔵 **自營商**: 買超 {dealer_net:,.0f} 張\n"
                else:
                    analysis += f"🔴 **自營商**: 賣超 {abs(dealer_net):,.0f} 張\n"
            else:
                analysis += "🔵 **自營商**: 中性\n"
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析法人數據失敗: {e}")
            return "❌ 法人數據分析失敗"
    
    def _analyze_news_data(self, query_info: Dict, data: Dict) -> str:
        """分析新聞數據"""
        try:
            news_data = data.get('news_data', [])
            if not news_data:
                return "❌ 無法獲取新聞數據"
            
            symbol = query_info.get('stock_symbol', 'N/A')
            stock_name = query_info.get('stock_name', '')
            
            analysis = f"📰 **新聞分析 ({symbol} {stock_name})**\n\n"
            
            # 統計新聞數量
            analysis += f"📈 **新聞總數**: {len(news_data)} 條\n\n"
            
            # 列出重要新聞標題
            analysis += "📋 **重要新聞**:\n"
            for i, news in enumerate(news_data[:5], 1):
                title = news.get('title', '無標題')
                source = news.get('source', 'unknown')
                analysis += f"{i}. {title} [{source}]\n"
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析新聞數據失敗: {e}")
            return "❌ 新聞數據分析失敗"
    
    def _analyze_technical_data(self, query_info: Dict, data: Dict) -> str:
        """分析技術數據"""
        try:
            stock_data = data.get('stock_data')
            if not stock_data:
                return "❌ 無法獲取技術數據"
            
            symbol = query_info.get('stock_symbol', 'N/A')
            stock_name = query_info.get('stock_name', '')
            current_price = stock_data.get('current_price', 'N/A')
            
            analysis = f"📈 **技術分析 ({symbol} {stock_name})**\n\n"
            analysis += f"💰 **當前價格**: {current_price}\n"
            analysis += f"🕐 **更新時間**: {stock_data.get('timestamp', 'N/A')}\n"
            
            # 這裡可以添加更多技術指標分析
            analysis += "\n⚠️ 注意: 詳細技術分析需要歷史價格數據\n"
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析技術數據失敗: {e}")
            return "❌ 技術數據分析失敗"
    
    def _analyze_general_data(self, query_info: Dict, data: Dict) -> str:
        """一般性數據分析"""
        try:
            symbol = query_info.get('stock_symbol', 'N/A')
            stock_name = query_info.get('stock_name', '')
            market = query_info.get('market', 'unknown')
            
            analysis = f"📊 **綜合分析 ({symbol} {stock_name})**\n\n"
            analysis += f"🏛️ **市場**: {market.upper()}\n"
            analysis += f"🕐 **分析時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # 數據可用性檢查
            available_data = []
            if data.get('stock_data'):
                available_data.append('股價數據')
            if data.get('institutional_data'):
                available_data.append('法人數據')
            if data.get('news_data'):
                available_data.append('新聞數據')
            
            analysis += f"✅ **可用數據**: {', '.join(available_data) if available_data else '無'}\n"
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"一般數據分析失敗: {e}")
            return "❌ 一般數據分析失敗"
    
    def _analyze_recommendation_data(self, query_info: Dict, data: Dict) -> str:
        """分析推薦數據"""
        try:
            recommendations = data.get('recommendations', [])
            if not recommendations:
                return "❌ 無法獲取法人投資數據進行推薦分析"
            
            analysis = f"🎯 **基於法人投資動向的股票推薦**\n\n"
            analysis += f"📊 **掃描結果**: 共分析 {len(recommendations)} 支股票\n\n"
            
            analysis += "🏆 **推薦排名** (依法人投資評分):\n\n"
            
            for i, rec in enumerate(recommendations, 1):
                symbol = rec.get('symbol', 'N/A')
                name = rec.get('name', 'N/A')
                score = rec.get('recommendation_score', 0)
                foreign_net = rec.get('foreign_net', 0)
                trust_net = rec.get('investment_trust_net', 0)
                dealer_net = rec.get('dealer_net', 0)
                
                # 判斷投資建議
                if score > 1000:
                    recommendation = "🔥 強力推薦"
                elif score > 500:
                    recommendation = "⭐ 推薦"
                elif score > 0:
                    recommendation = "👀 關注"
                else:
                    recommendation = "⚠️ 觀望"
                
                analysis += f"**{i}. {name} ({symbol})** - {recommendation}\n"
                analysis += f"   評分: {score:.1f}\n"
                
                # 法人動向描述
                if foreign_net > 0:
                    analysis += f"   外資: 買超 {foreign_net:,.0f} 張"
                else:
                    analysis += f"   外資: 賣超 {abs(foreign_net):,.0f} 張"
                
                if trust_net > 0:
                    analysis += f" | 投信: 買超 {trust_net:,.0f} 張"
                else:
                    analysis += f" | 投信: 賣超 {abs(trust_net):,.0f} 張"
                    
                analysis += "\n\n"
            
            analysis += "💡 **投資提醒**:\n"
            analysis += "• 法人買超不等於股價上漲保證\n"
            analysis += "• 建議結合技術面和基本面分析\n"
            analysis += "• 注意市場整體趨勢和風險\n"
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析推薦數據失敗: {e}")
            return "❌ 推薦數據分析失敗"
    
    def _generate_comprehensive_analysis(self, query_info: Dict, analysis_results: List[str], data: Dict) -> str:
        """使用AI生成綜合分析"""
        try:
            if not self.config['api']['openai_api_key']:
                # 如果沒有OpenAI API Key，返回簡單的拼接結果
                return self._simple_analysis_compilation(query_info, analysis_results)
            
            # 準備AI提示詞
            prompt = self._build_analysis_prompt(query_info, analysis_results, data)
            
            # 調用OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是專業的股票分析師，根據提供的數據給出深入、客觀的分析。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_analysis = response.choices[0].message.content.strip()
            
            # 組合最終結果
            final_result = f"{'='*60}\n"
            final_result += f"🎯 **智能股票分析報告**\n"
            final_result += f"{'='*60}\n\n"
            
            # 添加基礎分析
            for analysis in analysis_results:
                final_result += analysis + "\n\n"
            
            # 添加AI綜合分析
            final_result += f"🤖 **AI綜合分析**\n\n{ai_analysis}\n\n"
            final_result += f"{'='*60}\n"
            final_result += f"⚠️ **免責聲明**: 本分析僅供參考，不構成投資建議。投資有風險，請謹慎決策。\n"
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"生成綜合分析失敗: {e}")
            return self._simple_analysis_compilation(query_info, analysis_results)
    
    def _build_analysis_prompt(self, query_info: Dict, analysis_results: List[str], data: Dict) -> str:
        """構建AI分析提示詞"""
        symbol = query_info.get('stock_symbol', 'N/A')
        stock_name = query_info.get('stock_name', '')
        user_query = query_info.get('specific_request', '')
        
        prompt = f"""
請根據以下股票分析數據，為用戶問題提供專業分析：

用戶問題: {user_query}
股票: {symbol} {stock_name}

現有分析結果:
{chr(10).join(analysis_results)}

請提供:
1. 總結當前情況
2. 潛在風險和機會
3. 短期展望
4. 具體建議

請用繁體中文回答，並保持客觀專業。
        """
        
        return prompt.strip()
    
    def _simple_analysis_compilation(self, query_info: Dict, analysis_results: List[str]) -> str:
        """簡單的分析結果編譯（無AI）"""
        symbol = query_info.get('stock_symbol', 'N/A')
        stock_name = query_info.get('stock_name', '')
        
        final_result = f"{'='*60}\n"
        final_result += f"📊 **股票分析報告 - {symbol} {stock_name}**\n"
        final_result += f"{'='*60}\n\n"
        
        for analysis in analysis_results:
            final_result += analysis + "\n\n"
        
        final_result += f"{'='*60}\n"
        final_result += f"⚠️ **免責聲明**: 本分析僅供參考，不構成投資建議。\n"
        
        return final_result

def test_analyzer():
    """測試分析器 - 僅用於系統測試，不包含模擬數據"""
    print("分析器測試功能已移除，請使用 main.py 進行實際數據測試")

if __name__ == "__main__":
    test_analyzer()