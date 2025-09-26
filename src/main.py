#!/usr/bin/env python3
"""
智能股票分析系統
主程式入口點
"""

import sys
import argparse
from datetime import datetime
import yaml

from query_parser import QueryParser
from data_fetcher import DataFetcher
from analyzer import StockAnalyzer

class StockAnalysisSystem:
    def __init__(self, config_path="config.yaml"):
        """初始化股票分析系統"""
        self.config_path = config_path
        
        try:
            # 初始化各個模組
            self.query_parser = QueryParser(config_path)
            self.data_fetcher = DataFetcher(config_path)
            self.analyzer = StockAnalyzer(config_path)
            
            print("🚀 股票分析系統已啟動!")
            
        except FileNotFoundError:
            print(f"❌ 配置檔案 {config_path} 不存在")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 初始化失敗: {e}")
            sys.exit(1)
    
    def analyze_query(self, query: str) -> str:
        """分析用戶查詢"""
        try:
            print(f"🔍 正在分析問題: {query}")
            
            # 1. 解析查詢
            query_info = self.query_parser.parse_query(query)
            is_valid, validation_message = self.query_parser.validate_query(query_info)
            
            if not is_valid:
                return f"❌ 查詢無效: {validation_message}"
            
            print(f"✅ 查詢解析完成 (信心度: {query_info['confidence']:.1f})")
            print(f"📊 股票: {query_info.get('stock_symbol', 'N/A')} {query_info.get('stock_name', '')}")
            print(f"📈 分析類型: {', '.join(query_info['analysis_type'])}")
            
            # 2. 獲取數據
            print(f"📡 正在獲取實時數據...")
            
            # 判斷是否為推薦查詢
            if 'recommendation' in query_info['analysis_type']:
                # 推薦查詢：獲取法人推薦數據
                recommendations = self.data_fetcher.fetch_institutional_recommendations(10)
                data = {
                    'recommendations': recommendations,
                    'fetch_time': datetime.now().isoformat()
                }
            else:
                # 單股查詢：獲取指定股票數據
                symbol = query_info['stock_symbol']
                market = query_info.get('market', 'taiwan')
                data = self.data_fetcher.fetch_all_data(symbol, market)
            
            if not data:
                return "❌ 無法獲取股票數據，請檢查網絡連接或股票代號"
            
            print(f"✅ 數據獲取完成")
            
            # 3. 進行分析
            print(f"🤖 正在進行智能分析...")
            
            analysis_result = self.analyzer.analyze_data(query_info, data)
            
            print(f"✅ 分析完成")
            
            return analysis_result
            
        except KeyboardInterrupt:
            return "\n👋 分析已取消"
        except Exception as e:
            return f"❌ 分析過程中發生錯誤: {e}"
    
    def interactive_mode(self):
        """互動模式"""
        print("\n" + "="*60)
        print("🎯 歡迎使用智能股票分析系統")
        print("="*60)
        print("💡 使用範例:")
        print("   - 台積電最近法人怎麼看？")
        print("   - 2330 的新聞分析")
        print("   - AAPL 技術面分析")
        print("   - 鴻海這週的買賣超情況")
        print("\n📝 輸入 'quit' 或 'exit' 結束程式")
        print("="*60)
        
        while True:
            try:
                query = input("\n🤔 請輸入您的問題: ").strip()
                
                if query.lower() in ['quit', 'exit', '退出', 'q']:
                    print("👋 感謝使用，再見!")
                    break
                
                if not query:
                    print("⚠️ 請輸入有效問題")
                    continue
                
                # 分析查詢
                result = self.analyze_query(query)
                print(f"\n{result}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 感謝使用，再見!")
                break
            except EOFError:
                print("\n\n👋 感謝使用，再見!")
                break
    
    def single_query_mode(self, query: str):
        """單次查詢模式"""
        result = self.analyze_query(query)
        print(f"\n{result}")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="智能股票分析系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  %(prog)s                           # 啟動互動模式
  %(prog)s -q "台積電最近法人怎麼看？"    # 單次查詢
  %(prog)s -q "2330 新聞分析"         # 分析特定股票新聞
  %(prog)s -c custom_config.yaml     # 使用自定義配置檔案
        """
    )
    
    parser.add_argument(
        '-q', '--query',
        type=str,
        help='直接查詢股票分析'
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.yaml',
        help='配置檔案路徑 (預設: config.yaml)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='智能股票分析系統 v1.0.0'
    )
    
    args = parser.parse_args()
    
    try:
        # 初始化系統
        system = StockAnalysisSystem(args.config)
        
        if args.query:
            # 單次查詢模式
            system.single_query_mode(args.query)
        else:
            # 互動模式
            system.interactive_mode()
            
    except KeyboardInterrupt:
        print("\n👋 程式已終止")
    except Exception as e:
        print(f"❌ 程式執行錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()