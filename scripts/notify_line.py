#!/usr/bin/env python3
"""
LINE 通知推送工具

用法：
    python scripts/notify_line.py "訊息內容"
    python scripts/notify_line.py --file data/2026-02-13/holiday_snapshot.md

環境變數（可選，優先於內建設定）：
    LINE_CHANNEL_TOKEN - Channel access token
    LINE_USER_ID - Your user ID
"""

import sys
import os
import requests
from pathlib import Path

# === 載入 .env ===
env_file = Path(__file__).resolve().parent.parent / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

# === 設定（從 .env 或環境變數讀取） ===
CHANNEL_TOKEN = os.environ.get("LINE_CHANNEL_TOKEN", "")
USER_ID = os.environ.get("LINE_USER_ID", "")

if not CHANNEL_TOKEN or not USER_ID:
    print("錯誤：缺少 LINE_CHANNEL_TOKEN 或 LINE_USER_ID")
    print("請在 .env 檔案中設定，或設定環境變數")
    sys.exit(1)

# LINE 訊息上限 5000 字元
MAX_LENGTH = 5000


def send_message(text):
    """推送文字訊息到 LINE"""
    if len(text) > MAX_LENGTH:
        text = text[:MAX_LENGTH - 20] + "\n\n...（訊息過長已截斷）"

    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Authorization": f"Bearer {CHANNEL_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "to": USER_ID,
            "messages": [{"type": "text", "text": text}]
        },
        timeout=10
    )

    if resp.status_code == 200:
        print(f"LINE 通知發送成功")
    else:
        print(f"LINE 通知發送失敗: {resp.status_code} {resp.text}")

    return resp.status_code == 200


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/notify_line.py \"訊息內容\"")
        print("      python scripts/notify_line.py --file 檔案路徑")
        sys.exit(1)

    if sys.argv[1] == "--file" and len(sys.argv) >= 3:
        filepath = sys.argv[2]
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            send_message(content)
        else:
            print(f"檔案不存在: {filepath}")
            sys.exit(1)
    else:
        message = " ".join(sys.argv[1:])
        send_message(message)
