@echo off
echo Clearing RiskIntel360 credentials...
echo.

REM Remove the encrypted credentials file if it exists
if exist ".RiskIntel360_credentials.enc" (
    del ".RiskIntel360_credentials.enc"
    echo ✓ Removed encrypted credentials file
) else (
    echo ✓ No credentials file found
)

REM Run the Python script to clear any remaining credentials
python scripts/clear_credentials.py

echo.
echo ✅ Credentials cleared! The system now shows 0 credentials.
echo New users can now set up their AWS credentials through the UI.
echo.
pause