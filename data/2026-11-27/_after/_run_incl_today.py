# 盤後用：chip_analysis 改從今天起算（執行期替換，不改 scripts/），再跑指定掃描腳本
import sys, runpy
sys.path.insert(0, 'scripts')
from datetime import datetime, timedelta
import chip_analysis as ca
END = datetime(2026, 11, 27)
def _days(n_days=10):
    dates, cur = [], END
    while len(dates) < n_days:
        if cur.weekday() < 5: dates.append(cur.strftime('%Y%m%d'))
        cur -= timedelta(days=1)
    return dates
ca.get_trading_days = _days
script = sys.argv[1]
sys.argv = [script] + sys.argv[2:]
runpy.run_path(script, run_name='__main__')
