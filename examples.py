#!/usr/bin/env python3
"""
使用範例腳本
展示系統各種功能的實際操作
"""

import subprocess
import time

def run_example(title, command, description):
    """執行範例並顯示結果"""
    print("=" * 60)
    print(f"📖 **{title}**")
    print(f"說明: {description}")
    print(f"指令: {command}")
    print("-" * 60)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"⚠️ 警告: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("⏰ 執行超時，請檢查網路連線")
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
    
    print("\n")

def main():
    print("🚀 **台股智能分析系統 - 使用範例**")
    print("=" * 60)
    print("本腳本將展示系統的各種功能，每個範例之間會有短暫停頓")
    print("按 Ctrl+C 可隨時中斷")
    print()
    
    examples = [
        {
            "title": "範例1: 查詢台積電法人分析",
            "command": 'python3 main.py -q "2330法人分析"',
            "description": "查詢台積電的三大法人買賣超情況和投資建議"
        },
        {
            "title": "範例2: 獲取市場推薦股票",
            "command": 'python3 main.py -q "給我十檔可以進場參考的台股"',
            "description": "基於法人動向推薦值得關注的進場標的"
        },
        {
            "title": "範例3: 查詢廣達技術面分析", 
            "command": 'python3 main.py -q "廣達技術面分析"',
            "description": "分析廣達的技術指標和價格走勢"
        },
        {
            "title": "範例4: 個人持股組合分析",
            "command": 'python3 portfolio_analyzer.py',
            "description": "分析你在my_holdings.yaml中設定的個人持股表現"
        },
        {
            "title": "範例5: 查詢玉山金新聞分析",
            "command": 'python3 main.py -q "玉山金新聞分析"', 
            "description": "獲取玉山金的最新市場消息和分析"
        }
    ]
    
    try:
        for i, example in enumerate(examples, 1):
            print(f"\n🎯 準備執行範例 {i}/{len(examples)}")
            time.sleep(2)  # 給用戶時間閱讀
            
            run_example(
                example["title"],
                example["command"], 
                example["description"]
            )
            
            if i < len(examples):
                print("⏳ 3秒後執行下一個範例...")
                time.sleep(3)
        
        print("=" * 60)
        print("✅ **所有範例執行完畢！**")
        print()
        print("💡 **接下來你可以嘗試:**")
        print("• 編輯 my_holdings.yaml 加入你的實際持股")
        print("• 使用互動模式: python3 main.py")
        print("• 自訂查詢: python3 main.py -q '你的問題'")
        print()
        print("📚 **更多資訊請參考 README.md**")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 使用者中斷執行")
        print("📚 **可參考 README.md 了解更多功能**")

if __name__ == "__main__":
    main()