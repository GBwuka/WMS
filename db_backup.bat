rem *******************************Code Start*****************************
@echo off

set "Ymd=%date:~,4%%date:~5,2%%date:~8,2%"
"C:\Program Files\MySQL\MySQL Server 5.7\bin\"mysqldump --opt -u cts --password=123456 wms > .\db_backup\bbs_%Ymd%.sql
@echo on
rem pause
rem *******************************Code End*****************************