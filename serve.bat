@echo off
echo.
echo  Torreón RE Dashboard — Servidor local
echo  ======================================
echo  Abre en el navegador: http://localhost:8000/frontend/dashboard.html
echo.
cd /d C:\proyectos\real-estate
python -m http.server 8000
