cd /c/Users/walter.huang/Documents/github/investing/stock
export PYTHONIOENCODING=utf-8
for i in $(seq 1 24); do
  python3 scripts/fetch_institutional_top30.py 20261021 > data/2026-10-21/_after/inst_stdout.txt 2>&1
  f=data/cache/twse_t86_20261021.json
  if [ -f $f ] && [ $(stat -c %s $f) -gt 1000000 ]; then echo READY $(date); exit 0; fi
  sleep 600
done
echo TIMEOUT
