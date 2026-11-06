#!/usr/bin/env python3
"""chartlab 位置閘門（影子模式）：只記錄，不影響評分、推薦或任何決策。

對候選股呼叫 ../chartlab/gate_batch.py，把「支撐距離／量價狀態／趨勢結構／標記」
存起來，供 2~4 週後與結算結果比對，驗證閘門有沒有用。

用法：
    python scripts/chartlab_gate_shadow.py [代碼...]
    不給代碼時，讀當日 data/YYYY-MM-DD/price_position_check.json 的候選股。

輸出：
    data/YYYY-MM-DD/chartlab_gate.json        當日快照（整份覆蓋，可重算）
    data/shadow/chartlab_gate_log.jsonl       事件紀錄（只增不改，同一 asof 日不重複）

注意：只在收盤後／開盤前執行。盤中執行最後一根是未收完的K線，量與漲跌都不準。
失敗一律 exit 0：影子模式不能拖垮盤前流程。
"""
import io
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

os.environ['PYTHONUTF8'] = '1'
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).resolve().parent.parent
CHARTLAB_DIR = PROJECT_DIR.parent / "chartlab"
GATE_BATCH = CHARTLAB_DIR / "gate_batch.py"


def candidate_codes(today):
    codes = [a for a in sys.argv[1:] if a[:1].isdigit()]
    if codes:
        return codes
    p = PROJECT_DIR / "data" / today / "price_position_check.json"
    if p.exists():
        try:
            return [str(x['code']) for x in json.load(open(p, encoding='utf-8'))]
        except Exception as e:
            print(f"[chartlab_gate] 讀不到候選股：{e}")
    return []


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    if not GATE_BATCH.exists():
        print(f"[chartlab_gate] 找不到 {GATE_BATCH}，略過（影子模式）")
        return 0
    codes = [c for c in candidate_codes(today) if len(c) == 4]  # 個股；ETF 不分析
    if not codes:
        print("[chartlab_gate] 沒有候選股，略過")
        return 0

    out = PROJECT_DIR / "data" / today / "chartlab_gate.json"
    log = PROJECT_DIR / "data" / "shadow" / "chartlab_gate_log.jsonl"
    cmd = [sys.executable, str(GATE_BATCH), *codes, "--out", str(out), "--log", str(log)]
    try:
        r = subprocess.run(cmd, cwd=str(CHARTLAB_DIR), capture_output=True,
                           text=True, encoding='utf-8', timeout=300)
        print(r.stdout)
        if r.returncode != 0:
            print(f"[chartlab_gate] 失敗（略過，不影響流程）：{r.stderr[-300:]}")
    except Exception as e:
        print(f"[chartlab_gate] 例外（略過，不影響流程）：{e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
