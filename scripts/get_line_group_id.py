#!/usr/bin/env python3
"""
一次性工具：查詢 LINE Bot 最近收到的群組訊息，印出 Group ID
用法：在新群組傳一則訊息後，執行此腳本
"""

import os
import requests
from pathlib import Path

# 載入 .env
env_file = Path(__file__).resolve().parent.parent / ".env"
with open(env_file, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

TOKEN = os.environ.get("LINE_CHANNEL_TOKEN", "")

# 取得 Bot 最近收到的訊息（需要 Messaging API 有開 webhook）
# 改用 getGroupMemberProfile 探測法：嘗試已知群組以外的 groupId
# 實際上 LINE API 沒有 "list groups"，只能透過 webhook 取得

# 替代方案：請使用者直接到 manager.line.biz 查看群組頁面 URL
print("LINE API 不提供「列出所有群組」的功能。")
print()
print("最快的方法：")
print("1. 打開 manager.line.biz")
print("2. 點進你剛建立的新群組聊天")
print("3. 看瀏覽器網址列，格式類似：")
print("   https://manager.line.biz/account/xxxxx/chat/Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
print("   最後那段 C 開頭的就是 Group ID")
print()
print("或是：在新群組傳一則訊息，執行下方指令暫時改 webhook URL 來抓 ID。")
print()

# 驗證現有 GROUP_ID 的群組名稱供參考
existing = os.environ.get("LINE_GROUP_ID", "")
if existing:
    resp = requests.get(
        f"https://api.line.me/v2/bot/group/{existing}/summary",
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=10
    )
    data = resp.json()
    print(f"現有群組（LINE_GROUP_ID）：{data.get('groupName', '?')}  ID={existing}")
