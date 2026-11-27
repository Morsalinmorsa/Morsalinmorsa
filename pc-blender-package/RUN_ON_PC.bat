@echo off
REM Renders Shudhu Tomake in real 3D on this PC (Cycles + graphics card), then makes the MP4.
cd /d "%~dp0"
set "BL="
for /d %%D in ("C:\Program Files\Blender Foundation\Blender*") do if exist "%%D\blender.exe" set "BL=%%D\blender.exe"
if "%BL%"=="" (
  echo Blender not found. Install Blender 4.0 or newer from blender.org, or edit this file and set BL to blender.exe
  pause
  exit /b 1
)
echo Using "%BL%"
"%BL%" -b -P render_all_pc.py
echo.
echo Done! Your video: Shudhu_Tomake_3D_PC.mp4
pause
