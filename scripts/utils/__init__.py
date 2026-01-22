"""
工具模組
"""

from .cross_platform import (
    # 路徑處理
    get_project_root,
    get_data_path,
    get_tracking_file,
    get_analysis_dir,
    ensure_dir,
    path_exists,

    # 時區處理
    get_tw_now,
    get_tw_today,
    get_tw_today_compact,
    get_tw_yesterday,
    get_tw_yesterday_compact,
    get_weekday_tw,
    get_weekday_name_tw,
    is_trading_day,
    format_datetime_tw,

    # 檔案讀寫
    read_json,
    write_json,
    read_text,
    write_text,
    load_tracking,
    save_tracking,
    load_holdings,

    # 診斷
    diagnose_environment,
)

__all__ = [
    'get_project_root',
    'get_data_path',
    'get_tracking_file',
    'get_analysis_dir',
    'ensure_dir',
    'path_exists',
    'get_tw_now',
    'get_tw_today',
    'get_tw_today_compact',
    'get_tw_yesterday',
    'get_tw_yesterday_compact',
    'get_weekday_tw',
    'get_weekday_name_tw',
    'is_trading_day',
    'format_datetime_tw',
    'read_json',
    'write_json',
    'read_text',
    'write_text',
    'load_tracking',
    'save_tracking',
    'load_holdings',
    'diagnose_environment',
]
