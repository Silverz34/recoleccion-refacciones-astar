# Ejecutar el proyecto en Windows

Guía para correr `recoleccion-refacciones-astar` en Windows usando `uv`.

## 1. Instalar uv

Abre PowerShell y ejecuta:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Cierra PowerShell y ábrelo de nuevo. Verifica:

```powershell
uv --version
```

Alternativa:

```powershell
winget install --id=astral-sh.uv -e
```


## 2. Instalar dependencias y ejecutar

```powershell
cd C:\ruta\a\recoleccion-refacciones-astar
uv sync
uv run python src/rutas_almacen/main.py
```

## 3. Ejecuciones posteriores

Después de la primera vez solo necesitas:

```powershell
cd C:\ruta\a\recoleccion-refacciones-astar
uv run python src/rutas_almacen/main.py
```

## Referencia: cómo se ejecuta en NixOS

Solo en NixOS se necesita este paso extra, porque el sistema no trae librerías globales:

```bash
nix-shell -p uv "python314.withPackages (ps: [ ps.tkinter ])" stdenv.cc.cc.lib zlib
export UV_PYTHON_DOWNLOADS=never
export UV_PYTHON=$(which python3)
export LD_LIBRARY_PATH=$(nix-build '<nixpkgs>' -A stdenv.cc.cc.lib --no-out-link)/lib:$(nix-build '<nixpkgs>' -A zlib --no-out-link)/lib
uv venv --system-site-packages
uv sync
uv run python src/rutas_almacen/main.py
```
