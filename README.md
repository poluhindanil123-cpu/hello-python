# CI/CD на Python CLI с публикацией бинарников в GitHub Releases

Сборка Python CLI в один исполняемый файл через PyInstaller с автоматической публикацией в GitHub Releases.

> ⚠️ **Лабораторная работа выполняется в VS Code!**

---

## 📚 Что вы узнаете / вспомните

| Тема | Что рассматривается |
|------|---------------------|
| **Python** | Виртуальные окружения (`venv`), `pip`, запуск модулей (`python -m`) |
| **Тесты** | Встроенные тесты — `pytest` или `unittest` |
| **PyInstaller** | `--onefile`, упаковка интерпретатора и зависимостей |
| **Cross-compilation в Python** | Почему её нет (в отличие от Go) |
| **GitHub Actions** | Матричные сборки — 3 ОС параллельно |
| **softprops/action-gh-release** | Публикация артефактов |
| **SemVer** | Теги `v0.1.0`, `v0.2.0` |

---

## 🎯 Цель работы

Научиться автоматически собирать бинарники Python CLI под **Linux**, **macOS** и **Windows** и публиковать их в **GitHub Releases** при push тега `v*`.

### 🔑 Ключевое отличие от Go/Rust

- **Go/Rust** — один runner собирает под все платформы (cross-compilation).
- **Python** — для каждой ОС нужен **свой runner**, потому что PyInstaller встраивает **платформо-зависимый** интерпретатор.

### 📖 Что такое PyInstaller и GitHub Releases

> **PyInstaller** — инструмент, который превращает Python-скрипт в самодостаточный исполняемый файл: внутрь упаковывается интерпретатор Python, все зависимости и ваш код. Пользователь скачивает один файл — и запускает, без установки Python.

> **GitHub Releases** — раздел репозитория, где публикуются версии проекта: теги, описания и файлы для скачивания.

---

## 📁 Шаг 1. Структура проекта

Создайте в корневом каталоге текущего пользователя такую структуру:

```
hello-python/
├── .github/
│   └── workflows/
│       └── ci.yml
├── hello/
│   ├── __init__.py
│   └── greeting.py
├── tests/
│   └── test_greeting.py
├── .gitignore
├── main.py
├── pyproject.toml
└── requirements.txt
```

### 🚀 Создание структуры одной командой

**Git Bash / Linux / WSL / macOS:**

```bash
cd ~

mkdir -p hello-python/{.github/workflows,hello,tests} && \
cd hello-python && \

cat > pyproject.toml << 'EOF'
[project]
name = "hello-python"
version = "0.1.0"
description = "Demo Python CLI with PyInstaller and CI/CD"
requires-python = ">=3.10"

[project.scripts]
hello = "main:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
EOF

cat > requirements.txt << 'EOF'
pytest==8.3.3
pyinstaller==6.11.0
EOF

cat > hello/__init__.py << 'EOF'
__version__ = "0.1.0"
EOF

cat > hello/greeting.py << 'EOF'
def greet(name: str) -> str:
    return f"Hello, {name}!"


def sum_range(from_: int, to: int) -> int:
    return sum(range(from_, to + 1))
EOF

cat > tests/test_greeting.py << 'EOF'
from hello.greeting import greet, sum_range


def test_greet():
    assert greet("Python") == "Hello, Python!"
    assert greet("CI") == "Hello, CI!"


def test_sum_range():
    assert sum_range(1, 10) == 55
    assert sum_range(1, 100) == 5050
EOF

cat > main.py << 'EOF'
import sys
import platform

from hello import __version__
from hello.greeting import greet, sum_range


def main() -> int:
    print(f"hello-python version {__version__}")
    print("Hello from Python! 🐍📦")
    print(f"OS: {platform.system().lower()}")
    print(f"Arch: {platform.machine()}")
    print(greet("GitHub"))
    print(f"Sum 1..10 = {sum_range(1, 10)}")

    if len(sys.argv) > 1:
        print("Аргументы:")
        for i, arg in enumerate(sys.argv[1:], start=1):
            print(f"  {i}: {arg}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
EOF
```

---

## ⚙️ GitHub Actions (`.github/workflows/ci.yml`)

```yaml
name: Python CI/CD

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:

jobs:
  # ===== Job 1: CI — линтер и тесты =====
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Lint with ruff
        run: |
          pip install ruff==0.7.1
          ruff check .
          ruff format --check .

      - name: Run tests
        run: python -m pytest -v

  # ===== Job 2: CD — публикация бинарников по тегу =====
  release:
    needs: test
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ${{ matrix.os }}

    permissions:
      contents: write

    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            artifact: hello-python-linux-x64
          - os: macos-14
            artifact: hello-python-macos-arm64
          - os: windows-latest
            artifact: hello-python-windows-x64.exe

    steps:
      - uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Build with PyInstaller
        run:  python -m PyInstaller --onefile --name hello-python main.py

      - name: Rename binary (Unix)
        if: runner.os != 'Windows'
        run: mv dist/hello-python dist/${{ matrix.artifact }}

      - name: Rename binary (Windows)
        if: runner.os == 'Windows'
        run: mv dist/hello-python.exe dist/${{ matrix.artifact }}

      - name: Upload to Release
        uses: softprops/action-gh-release@v2
        with:
          files: dist/${{ matrix.artifact }}
          generate_release_notes: true
```

---

## 🚫 `.gitignore`

```gitignore
__pycache__/
*.pyc
.venv/
venv/
.env
build/
dist/
*.spec
.pytest_cache/
.ruff_cache/
.idea/
.vscode/
*.egg-info/
```

**Проверка результата:**

```bash
echo "✅ Структура создана:"
find . -type f | sort
```

---

## 🧪 Шаг 2. Тесты в Docker

> **Python на хосте не нужен** — всё выполняется внутри контейнера.

### Git Bash / Linux / WSL / macOS

```bash
cd ~/hello-python
docker run --rm \
  -u "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -v "$(pwd)":/app \
  -v ~/.pip-docker-cache:/tmp/.cache/pip \
  -w /app \
  python:3.12-slim \
  sh -c "pip install --cache-dir=/tmp/.cache/pip -r requirements.txt && python -m pytest -v"
```

### PowerShell (Windows)

```powershell
cd ~/hello-python
docker run --rm `
  -v "${PWD}:/app" `
  -w /app `
  python:3.12-slim `
  sh -c "pip install -r requirements.txt && python -m pytest -v"
```

**Ожидаемый вывод:**

```
tests/test_greeting.py::test_greet PASSED
tests/test_greeting.py::test_sum_range PASSED
========================= 2 passed in 0.12s =========================
```

---

## 📦 Шаг 3. Локальная сборка бинарника через PyInstaller

### Git Bash / Linux / WSL / macOS

```bash
cd ~/hello-python
MSYS_NO_PATHCONV=1 docker run --rm \
  -u "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -v "$(pwd)":/app \
  -v ~/.pip-docker-cache:/tmp/.cache/pip \
  -w /app \
  python:3.12 \
  sh -c "pip install --cache-dir=/tmp/.cache/pip -r requirements.txt && \
         python -m PyInstaller --onefile --name hello-python main.py && \
         ls -la dist/"
```

> 💡 Флаг `MSYS_NO_PATHCONV=1` нужен, чтобы Git Bash на Windows не превратил `/app` в `C:/Program Files/Git/app`.

### PowerShell (Windows)

```powershell
cd ~/hello-python
docker run --rm `
  -v "${PWD}:/app" `
  -w /app `
  python:3.12 `
  sh -c "pip install -r requirements.txt && python -m PyInstaller --onefile --name hello-python main.py"
```

---

## ▶️ Запуск бинарника в чистом Debian

После сборки в папке `dist/` появится файл `hello-python` (Linux-бинарник). Запустите его в чистом контейнере:

```bash
MSYS_NO_PATHCONV=1 docker run --rm \
  -v "$(pwd)/dist":/dist \
  debian:stable-slim \
  /dist/hello-python
```

**Ожидаемый вывод:**

```
hello-python version 0.1.0
Hello from Python! 🐍📦
OS: linux
Arch: x86_64
Hello, GitHub!
Sum 1..10 = 55
```

---

## ⚠️ Важно про cross-compilation

> Бинарник, собранный в Linux-контейнере, **не запустится** на Windows или macOS. PyInstaller **не умеет cross-compilation** — под каждую ОС нужна своя сборка. Именно поэтому в CI мы используем **матрицу с тремя runner'ами**.

---

## 📋 Краткая шпаргалка

```bash
# 1. Создать структуру
cd ~ && mkdir -p hello-python/{.github/workflows,hello,tests} && cd hello-python
# ... (файлы из шага 1)

# 2. Тесты в Docker
docker run --rm -v "$(pwd)":/app -w /app python:3.12-slim \
  sh -c "pip install -r requirements.txt && python -m pytest -v"

# 3. Сборка бинарника через PyInstaller
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app -w /app python:3.12 \
  sh -c "pip install -r requirements.txt && python -m PyInstaller --onefile --name hello-python main.py"

# 4. Запуск в чистом Debian
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)/dist":/dist debian:stable-slim /dist/hello-python

# 5. Создать репозиторий на GitHub (вручную)

# 6. Запушить
git init && git add . && git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<USERNAME>/hello-python.git
git push -u origin main

# 7. Создать тег и запустить релиз
git tag v0.1.0
git push origin v0.1.0
```

---

## 🎁 Что происходит при push тега `v*`

| Шаг | Действие |
|-----|----------|
| 1 | Запускается Job `test` — линтер `ruff` + тесты `pytest` |
| 2 | Если тесты прошли — запускается Job `release` |
| 3 | Параллельно на 3 ОС (`ubuntu-latest`, `macos-14`, `windows-latest`) собираются бинарники через PyInstaller |
| 4 | Каждый бинарник переименовывается в уникальное имя (например, `hello-python-linux-x64`) |
| 5 | `softprops/action-gh-release@v2` публикует все три файла в GitHub Releases с автоматическими release notes |

**Результат:** пользователь заходит в раздел **Releases** на GitHub и скачивает готовый бинарник под свою ОС — без установки Python.

---

## 💡 Полезные замечания

| Ситуация | Что использовать |
|----------|------------------|
| Ошибка `C:/Program Files/Git/...` | `MSYS_NO_PATHCONV=1` перед `docker run` |
| Нужно ускорить сборку в Docker | Кэш pip через `-v ~/.pip-docker-cache:/tmp/.cache/pip` |
| Ошибка `remote origin already exists` | `git remote remove origin` и добавить заново с правильным URL |
| Предупреждения `LF will be replaced by CRLF` | Добавить `.gitattributes` с `* text=auto eol=lf` |
| Push в `main` не запускает релиз | Релиз запускается только по тегу — сделайте `git tag v0.1.0 && git push origin v0.1.0` |
