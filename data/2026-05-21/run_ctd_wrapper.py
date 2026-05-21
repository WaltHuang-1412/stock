import sys, os, io

# Fix: prevent TextIOWrapper from closing shared buffer on garbage collection
# by using reconfigure instead of replacing

# Patch sys.stdout to a real file-backed stream
log = open('data/2026-05-21/ctd_log.txt', 'w', encoding='utf-8')
sys.stdout = log
sys.stderr = log

# Now patch the io.TextIOWrapper behavior
_orig_textio = io.TextIOWrapper.__init__

os.chdir(r'C:\Users\walter.huang\Documents\github\stock')
sys.path.insert(0, 'scripts')

# Pre-import and patch reversal_alert to avoid stdout issues
import importlib.util

# First load reversal_alert with our file-based stdout already set
spec = importlib.util.spec_from_file_location('reversal_alert', 'scripts/reversal_alert.py')
ra = importlib.util.module_from_spec(spec)
sys.modules['reversal_alert'] = ra
spec.loader.exec_module(ra)

# Now load catalyst_theme_detector
spec2 = importlib.util.spec_from_file_location('catalyst_theme_detector', 'scripts/catalyst_theme_detector.py')
ctd = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(ctd)

# Run the scan
ctd.scan('2026-05-21', lookback=7)
log.flush()
log.close()
