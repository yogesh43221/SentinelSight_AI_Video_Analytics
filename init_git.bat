@echo off
echo Initializing Git Repository...
git init

echo Adding files...
git add .

echo Committing files...
git commit -m "Initial commit of SentinelSight AI Platform"

echo Setting up Main branch...
git branch -M main

echo Adding Remote Origin...
git remote add origin https://github.com/yogesh43221/SentinelSight_AI_Video_Analytics

echo.
echo ========================================================
echo Git Setup Complete!
echo Now run this command to upload code:
echo git push -u origin main
echo ========================================================
