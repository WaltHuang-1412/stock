#!/usr/bin/env python3
"""
股票代碼驗證工具
用途：檢查股票清單中哪些代碼可能已下市或無效
執行方式：python3 scripts/validate_stock_codes.py
"""

import yfinance as yf
import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def validate_stock_code(code):
    """驗證單一股票代碼是否有效"""
    try:
        ticker = f"{code}.TW"
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")

        if hist.empty:
            return False, "無價格數據"

        # 檢查是否有成交量（避免假資料）
        if hist['Volume'].iloc[-1] == 0:
            return False, "無成交量"

        return True, f"有效（收盤價：{hist['Close'].iloc[-1]:.2f}）"

    except Exception as e:
        return False, f"錯誤：{str(e)[:30]}..."

def get_stock_list_from_detector():
    """從 institutional_positioning_detector.py 獲取股票清單"""
    try:
        # 直接導入模組
        import sys
        sys.path.append('scripts')
        from institutional_positioning_detector import FOCUS_STOCKS
        return FOCUS_STOCKS

    except Exception as e:
        # 手動定義常見股票清單進行測試
        print(f"⚠️ 無法導入股票清單，使用預設清單進行測試")
        return [
            '2330', '2454', '2382', '2408', '2344', '2303',  # 半導體
            '2890', '2801', '2885', '2883',  # 金融
            '1303', '1301', '2002',  # 傳產
        ]

def main():
    """主程式"""
    print("🔍 股票代碼驗證工具")
    print("=" * 60)

    # 獲取股票清單
    stock_codes = get_stock_list_from_detector()
    if not stock_codes:
        print("❌ 無法獲取股票清單")
        return

    print(f"📊 共 {len(stock_codes)} 檔股票待驗證\n")

    valid_stocks = []
    invalid_stocks = []

    # 逐一驗證
    for i, code in enumerate(stock_codes, 1):
        print(f"[{i:3d}/{len(stock_codes)}] 檢查 {code}...", end=" ")

        is_valid, message = validate_stock_code(code)

        if is_valid:
            print(f"✅ {message}")
            valid_stocks.append(code)
        else:
            print(f"❌ {message}")
            invalid_stocks.append((code, message))

    # 統計結果
    print("\n" + "=" * 60)
    print("📈 驗證結果統計")
    print(f"✅ 有效股票：{len(valid_stocks)} 檔")
    print(f"❌ 無效股票：{len(invalid_stocks)} 檔")
    print(f"📊 有效率：{len(valid_stocks)/(len(stock_codes))*100:.1f}%")

    # 列出無效股票
    if invalid_stocks:
        print(f"\n❌ 需要移除的股票代碼：")
        for code, reason in invalid_stocks:
            print(f"   {code} - {reason}")

        print(f"\n🔧 建議修改 institutional_positioning_detector.py：")
        print("   移除以上股票代碼以避免 API 錯誤")
    else:
        print(f"\n🎉 所有股票代碼都有效！")

if __name__ == '__main__':
    main()