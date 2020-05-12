import sys
from cx_Freeze import setup, Executable
import os

os.environ['TCL_LIBRARY'] = "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python36\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python36\\tcl\\tk8.6"

base = None

if sys.platform == 'win32':
    base = 'Win32GUI'

includes = [r'queue', r'idna.idnadata']

include_files = ["C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python36\\DLLs\\tcl86t.dll",
                 "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python36\\DLLs\\tk86t.dll",
                 'C:\\Users\\Administrator\\PycharmProjects\\Barometer\\emotionmanage-client\\VersionInfo.xml']

options = {
    'build_exe': {'includes': includes, 'include_files': include_files},
}

executables = [Executable(script='update.py', base=base, targetName='update.exe')]

setup(
    name="update",
    version="1.0.0",
    author='diaokongzhongxin',
    author_email='zhangpengjie1993@163.com',
    description="dangjian updatesystem of barometer",
    options=options,
    executables=executables,
)
