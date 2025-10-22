@echo off
echo ========================================
echo RiskIntel360 - Stop Database
echo ========================================
echo.

echo 🛑 Stopping PostgreSQL database...
docker stop riskintel360-postgres

echo 🗑️  Removing PostgreSQL container...
docker rm riskintel360-postgres

echo ✅ Database stopped and removed
pause