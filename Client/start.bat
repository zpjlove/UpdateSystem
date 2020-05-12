::@echo off 
::if "%1" == "h" goto begin 
::mshta vbscript:createobject("wscript.shell").run("""%~nx0"" h",0)(window.close)&&exit 
:begin 
@echo off
set path=%~dp0
%path%C:\Users\Administrator\AppData\Local\Programs\Python\Python38\python.exe %path%client.py
@echo on
@echo off
pause