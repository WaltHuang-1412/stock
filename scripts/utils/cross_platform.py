"""
跨平台相容性工具模組
解決 Windows/Mac 系統差異問題

P0-1: 路徑統一 (pathlib)
P0-2: 時區統一 (Asia/Taipei)
P0-3: 編碼統一 (UTF-8)
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Union, Any

# 嘗試導入 pytz，如果沒有則提供降級方案
try:
    import pytz
    TW_TZ = pytz.timezone('Asia/Taipei')
    HAS_PYTZ = True
except ImportError:
    TW_TZ = None
    HAS_PYTZ = False
    print("⚠️ 警告: pytz 未安裝，時區功能受限。請執行: pip install pytz")


# ============================================================
# P0-1: 路徑處理
# ============================================================

def get_project_root() -> Path:
    """取得專案根目錄"""
    # 從 scripts/utils/ 往上兩層
    return Path(__file__).parent.parent.parent


def get_data_path(*parts: str) -> Path:
    """
    取得 data 目錄下的路徑

    範例:
        get_data_path('tracking', 'tracking_2026-01-22.json')
        → /project/data/tracking/tracking_2026-01-22.json
    """
    return get_project_root() / 'data' / Path(*parts)


def get_tracking_file(date_str: str) -> Path:
    """取得 tracking 檔案路徑"""
    return get_data_path('tracking', f'tracking_{date_str}.json')


def get_analysis_dir(date_str: str) -> Path:
    """取得分析目錄路徑"""
    return get_data_path(date_str)


def ensure_dir(path: Path) -> Path:
    """確保目錄存在"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def path_exists(path: Union[str, Path]) -> bool:
    """檢查路徑是否存在"""
    return Path(path).exists()


# ============================================================
# P0-2: 時區處理
# ============================================================

def get_tw_now() -> datetime:
    """
    取得台灣時間 (UTC+8)

    即使系統時區不是台灣，也會返回正確的台灣時間
    """
    if HAS_PYTZ:
        return datetime.now(TW_TZ)
    else:
        # 降級方案：假設系統時區正確（Windows 通常是）
        return datetime.now()


def get_tw_today() -> str:
    """取得今日日期字串 (YYYY-MM-DD)"""
    return get_tw_now().strftime('%Y-%m-%d')


def get_tw_today_compact() -> str:
    """取得今日日期字串 (YYYYMMDD)"""
    return get_tw_now().strftime('%Y%m%d')


def get_tw_yesterday() -> str:
    """取得昨日日期字串 (YYYY-MM-DD)"""
    yesterday = get_tw_now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')


def get_tw_yesterday_compact() -> str:
    """取得昨日日期字串 (YYYYMMDD)"""
    yesterday = get_tw_now() - timedelta(days=1)
    return yesterday.strftime('%Y%m%d')


def get_weekday_tw() -> int:
    """取得今日星期幾 (0=週一, 6=週日)"""
    return get_tw_now().weekday()


def get_weekday_name_tw() -> str:
    """取得今日星期名稱"""
    names = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
    return names[get_weekday_tw()]


def is_trading_day() -> bool:
    """判斷今日是否為交易日（週一至週五）"""
    return get_weekday_tw() < 5


def format_datetime_tw(dt: Optional[datetime] = None, fmt: str = '%Y-%m-%d %H:%M') -> str:
    """格式化日期時間"""
    if dt is None:
        dt = get_tw_now()
    return dt.strftime(fmt)


# ============================================================
# P0-3: 檔案讀寫（UTF-8 編碼）
# ============================================================

def read_json(file_path: Union[str, Path]) -> Optional[dict]:
    """
    讀取 JSON 檔案（強制 UTF-8）

    Returns:
        dict 或 None（檔案不存在或解析失敗）
    """
    path = Path(file_path)
    if not path.exists():
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"❌ 讀取 JSON 失敗: {path}, 錯誤: {e}")
        return None


def write_json(file_path: Union[str, Path], data: Any, indent: int = 2) -> bool:
    """
    寫入 JSON 檔案（強制 UTF-8，保留中文）

    Returns:
        True 成功, False 失敗
    """
    path = Path(file_path)

    # 確保目錄存在
    ensure_dir(path.parent)

    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        print(f"❌ 寫入 JSON 失敗: {path}, 錯誤: {e}")
        return False


def read_text(file_path: Union[str, Path]) -> Optional[str]:
    """
    讀取文字檔案（強制 UTF-8）
    """
    path = Path(file_path)
    if not path.exists():
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError as e:
        print(f"❌ 讀取文字檔失敗: {path}, 錯誤: {e}")
        return None


def write_text(file_path: Union[str, Path], content: str) -> bool:
    """
    寫入文字檔案（強制 UTF-8）
    """
    path = Path(file_path)

    # 確保目錄存在
    ensure_dir(path.parent)

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"❌ 寫入文字檔失敗: {path}, 錯誤: {e}")
        return False


# ============================================================
# 便捷函數
# ============================================================

def load_tracking(date_str: Optional[str] = None) -> Optional[dict]:
    """載入 tracking 檔案"""
    if date_str is None:
        date_str = get_tw_today()
    return read_json(get_tracking_file(date_str))


def save_tracking(data: dict, date_str: Optional[str] = None) -> bool:
    """儲存 tracking 檔案"""
    if date_str is None:
        date_str = get_tw_today()
    return write_json(get_tracking_file(date_str), data)


def load_holdings() -> Optional[dict]:
    """載入持股檔案"""
    import yaml
    holdings_path = get_project_root() / 'portfolio' / 'my_holdings.yaml'
    if not holdings_path.exists():
        return None

    try:
        with open(holdings_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 讀取持股檔失敗: {e}")
        return None


# ============================================================
# 診斷工具
# ============================================================

def diagnose_environment():
    """診斷執行環境"""
    print("=" * 50)
    print("🔍 跨平台環境診斷")
    print("=" * 50)

    # 系統資訊
    print(f"\n📌 系統資訊:")
    print(f"   平台: {sys.platform}")
    print(f"   Python: {sys.version}")
    print(f"   編碼: {sys.getdefaultencoding()}")
    print(f"   檔案系統編碼: {sys.getfilesystemencoding()}")

    # 時區資訊
    print(f"\n⏰ 時區資訊:")
    print(f"   pytz 可用: {HAS_PYTZ}")
    print(f"   台灣時間: {get_tw_now()}")
    print(f"   今日: {get_tw_today()} ({get_weekday_name_tw()})")
    print(f"   交易日: {'是' if is_trading_day() else '否'}")

    # 路徑資訊
    print(f"\n📁 路徑資訊:")
    print(f"   專案根目錄: {get_project_root()}")
    print(f"   data 目錄存在: {path_exists(get_project_root() / 'data')}")
    print(f"   tracking 目錄存在: {path_exists(get_data_path('tracking'))}")

    # 測試路徑
    test_path = get_tracking_file('2026-01-22')
    print(f"   測試路徑: {test_path}")
    print(f"   路徑分隔符: {os.sep}")

    print("\n" + "=" * 50)
    print("✅ 診斷完成")
    print("=" * 50)


if __name__ == '__main__':
    diagnose_environment()
