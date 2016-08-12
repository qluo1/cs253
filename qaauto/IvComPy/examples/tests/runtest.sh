scriptname=testDSClient.py
logfile=utestDSClient.151223

rm ../logs/$logfile
python $scriptname
echo ---------------[LOG]---------------------------
cat ../logs/$logfile
echo ---------------[LOG]---------------------------
