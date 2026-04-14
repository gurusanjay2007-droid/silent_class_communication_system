@echo off
echo Attempting to push changes to GitHub...

:: Add all changes
git add .

:: Commit with a timestamp
set commit_msg="Update on %date% at %time%"
git commit -m %commit_msg%

:: Push to the main branch
git push origin main

echo.
if %errorlevel% neq 0 (
    echo [ERROR] Push failed. Please check the messages above.
) else (
    echo [SUCCESS] Changes pushed to GitHub! Vercel will now redeploy.
)

pause
