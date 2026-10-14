#!/usr/bin/env python3
"""PreToolUse: блокирует правки защищённых файлов (.env, .git/, lock-файлы)."""
import json
import os
import sys

LOCK_NAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "gradle.lockfile",
    "poetry.lock", "Cargo.lock", "Pipfile.lock", "composer.lock",
}


def reason(path):
    parts = os.path.normpath(path).split(os.sep)
    name = parts[-1]
    if ".git" in parts[:-1]:
        return "каталог .git/ защищён"
    if name == ".env" or name.startswith(".env."):
        return "файлы .env содержат секреты"
    if name in LOCK_NAMES or name.endswith(".lock"):
        return "lock-файлы генерируются менеджером зависимостей"
    return None


def main():
    data = json.load(sys.stdin)
    path = data.get("tool_input", {}).get("file_path", "")
    why = reason(path) if path else None
    if why:
        print(f"Заблокировано: {path}: {why}. Не редактируй этот файл.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
