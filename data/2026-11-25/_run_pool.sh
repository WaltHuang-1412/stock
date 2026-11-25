#!/bin/bash
cd /c/Users/walter.huang/Documents/github/investing/stock
export PYTHONIOENCODING=utf-8
D=data/2026-11-25
POOL=$(cat $D/_pool.txt)
python3 scripts/reversal_alert.py $POOL --output-dir $D/cand > $D/_rev_pool.txt 2>&1
python3 scripts/chip_analysis.py $POOL --days 10 > $D/chip_pool.txt 2>&1
python3 scripts/check_price_position.py $POOL > $D/_pp.txt 2>&1
python3 scripts/check_revenue_yoy.py --update-cache $POOL > $D/_rev_upd.txt 2>&1
python3 scripts/check_revenue_yoy.py $POOL > $D/_rev.txt 2>&1
python3 scripts/check_eps_quarterly.py $POOL --update-cache > $D/_eps.txt 2>&1
python3 scripts/check_foreign_ratio.py $POOL > $D/_fr.txt 2>&1
touch $D/_pool_done
