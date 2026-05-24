@echo off
REM ─── Plantilla FlappyBird — Lanzador Windows ────────────────────────────
REM Ejecuta el juego desde la raíz del proyecto.
REM Requisito: python en el PATH e instalado pygame (pip install -r requirements.txt)
cd /d "%~dp0"
python src\main.py
pause
