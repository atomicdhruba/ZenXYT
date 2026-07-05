@echo off
title Zen MetaBot Master Bot v2.0
color 0B

echo ==========================================
echo       ZENXYT MASTER BOT LAUNCHER
echo ==========================================
echo.
echo Starting Multi-AI Debate Engine (GUI Mode)...
echo.

:: This line forces the terminal to open in the exact folder where the bot lives
cd /d "%~dp0"

:: Launch the bot
python bot.py

:: SAFETY NET: If the bot crashes or finishes, this keeps the window open so you can read the error!
echo.
pause