# 執行期包裝：tracking 的 holding_days 為 'D0/10' 字串時 preflight_check.check_d10_settlement 會 TypeError
# （不修改 scripts/，僅於執行期把字串轉成整數後交回原邏輯）
import sys, json, re
sys.path.insert(0, 'scripts')
sys.argv = ['preflight_check.py', '--mode', 'after_market', '--fix']
import preflight_check as pc
_orig_load = json.load
def _load(f, *a, **k):
    d = _orig_load(f, *a, **k)
    if isinstance(d, dict) and isinstance(d.get('recommendations'), list):
        for r in d['recommendations']:
            h = r.get('holding_days') if isinstance(r, dict) else None
            if isinstance(h, str):
                m = re.search(r'D(\d+)', h)
                r['holding_days'] = int(m.group(1)) if m else 0
    return d
_orig = pc.check_d10_settlement
def patched(today):
    pc.json.load = _load
    try: return _orig(today)
    finally: pc.json.load = _orig_load
pc.check_d10_settlement = patched
pc.main()
