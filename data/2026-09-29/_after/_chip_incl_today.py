# 盤後用：chip_analysis 預設從「昨天」起算（盤前情境），盤後 T86 已公布時改從今天起算。
# 只在執行期替換 get_trading_days，不修改 scripts/chip_analysis.py。
import sys, json
sys.path.insert(0, 'scripts')
from datetime import datetime, timedelta
import chip_analysis as ca
END = datetime(2026, 9, 29)
def _days(n_days=10):
    dates, cur = [], END
    while len(dates) < n_days:
        if cur.weekday() < 5: dates.append(cur.strftime('%Y%m%d'))
        cur -= timedelta(days=1)
    return dates
ca.get_trading_days = _days
out = {}
for code in sys.argv[2:]:
    r = ca.analyze_chip_history(code, 10)
    if r:
        ca.print_chip_report(r)
        out[code] = r
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
