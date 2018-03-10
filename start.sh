if [ -f 'terminated' ];then
rm 'terminated'
fi
nohup python3 Trader.py >/dev/null 2>&1 &
