@echo off
echo ================================
echo   INSTALL PYTHON REQUIREMENTS
echo ================================

REM Kiểm tra Python có tồn tại không
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
echo [ERROR] Khong tim thay Python. Hay cai Python truoc!
pause
exit /b
)

REM Nâng cấp pip
echo.
echo [INFO] Dang nang cap pip...
python -m pip install --upgrade pip

REM Cài thư viện từ requirements.txt
echo.
echo [INFO] Dang cai dat thu vien...
python -m pip install -r .\data\requirements.txt

REM Kiểm tra kết quả
IF %ERRORLEVEL% EQU 0 (
echo.
echo [SUCCESS] Cai dat hoan tat!
) ELSE (
echo.
echo [ERROR] Co loi xay ra khi cai dat!
)

echo.
pause
