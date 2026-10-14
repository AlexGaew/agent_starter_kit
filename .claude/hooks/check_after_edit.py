#!/usr/bin/env python3
"""PostToolUse: проверка файла после правки.

Встроено: .json (разбор), .js (node --check), .py (py_compile).
Под стек проекта добавь свои проверки в PROJECT_CHECKS ниже (это единственное место для правки).
Ошибка: код выхода 2 и текст в stderr, агент видит его и исправляет файл.
"""
import json
import os
import py_compile
import subprocess
import sys

# Проверки проекта. Ключ: расширение файла. Значение:
#   "requires": файлы в корне проекта, без которых проверка пропускается (скелета ещё нет)
#   "cmd": команда; {path} подставляется путём правленого файла; запускается в корне проекта
#   "timeout": секунды
# Заполняется после опроса `new-project-interview`. Примеры:
#   ".java": {"requires": ["pom.xml", "mvnw"], "cmd": ["./mvnw", "-q", "spotless:apply"], "timeout": 120},
#   ".ts":   {"requires": ["package.json"], "cmd": ["npx", "eslint", "{path}"], "timeout": 60},
#   ".py":   {"requires": ["pyproject.toml"], "cmd": ["ruff", "check", "{path}"], "timeout": 30},
PROJECT_CHECKS = {}


def fail(message):
    print(message, file=sys.stderr)
    return 2


def run(cmd, cwd, timeout, label):
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return fail(f"{label}: не уложился в {timeout} секунд")
    except FileNotFoundError:
        return 0  # инструмента нет на машине, проверять нечем
    if result.returncode != 0:
        return fail(f"{label} завершился с ошибкой:\n" + (result.stdout + result.stderr)[-2000:])
    return 0


def check_project(ext, path, root):
    spec = PROJECT_CHECKS[ext]
    if any(not os.path.isfile(os.path.join(root, name)) for name in spec.get("requires", [])):
        return 0
    cmd = [part.replace("{path}", path) for part in spec["cmd"]]
    return run(cmd, root, spec.get("timeout", 60), " ".join(cmd[:2]))


def check_js(path):
    return run(["node", "--check", path], None, 30, f"node --check {path}")


def check_py(path):
    try:
        py_compile.compile(path, doraise=True)
    except py_compile.PyCompileError as e:
        return fail(f"Синтаксическая ошибка в {path}:\n{e}")
    return 0


def check_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            json.load(f)
    except (ValueError, OSError) as e:
        return fail(f"Невалидный JSON в {path}: {e}")
    return 0


BUILTIN = {".js": check_js, ".py": check_py, ".json": check_json}


def main():
    data = json.load(sys.stdin)
    path = data.get("tool_input", {}).get("file_path", "")
    skip_dirs = {"node_modules", ".venv", "target", "build", "dist", ".git"}
    if not path or not os.path.isfile(path) or skip_dirs & set(path.split(os.sep)):
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    ext = os.path.splitext(path)[1]
    if ext in PROJECT_CHECKS:
        return check_project(ext, path, root)
    if ext in BUILTIN:
        return BUILTIN[ext](path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
