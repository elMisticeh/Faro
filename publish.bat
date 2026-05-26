@echo off
echo.
echo  CAMPO — Publicar nueva version
echo  ================================

REM Copia frontend a docs (GitHub Pages)
copy /Y "frontend\dashboard.html" "docs\index.html" >nul
echo  [OK] docs\index.html actualizado

REM Commit y push
cd /d %~dp0
git add docs\index.html frontend\dashboard.html CHANGELOG.md
git status --short

set /p MSG=Mensaje del commit (Enter para usar "release: update dashboard"):
if "%MSG%"=="" set MSG=release: update dashboard

git commit -m "%MSG%"
git push

echo.
echo  Listo! GitHub Pages se actualiza en ~1 minuto.
echo  URL: https://[tu-usuario].github.io/[nombre-repo]/
echo.
pause
