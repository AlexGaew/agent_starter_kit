#!/usr/bin/env python3
"""PreToolUse (Bash): блокирует команды, которые читают .env или пишут в .git/, .env*, lock-файлы.

Это эвристика по тексту команды, а не песочница: её можно обойти косвенными способами
(переменные, скрипты, eval). Она закрывает типовые случаи: redirect, tee, sed -i, rm, mv, cp,
git config. Дополняет block_protected.py, который защищает инструменты Edit и Write.
"""
import json
import re
import sys

ENV_FILE = re.compile(r"(?<![\w.-])\.env(\.[\w-]+)*(?![\w-])")
GIT_DIR = re.compile(r"(?<![\w-])\.git(?:/|$|['\"\s])")
LOCK_FILE = re.compile(
    r"(?<![\w.-])(?:package-lock\.json|yarn\.lock|pnpm-lock\.yaml|gradle\.lockfile|"
    r"[\w.-]+\.lock)(?![\w-])"
)

NOISE = re.compile(r"\d*>&\d+|\d*>\s*/dev/null")
WRITE = re.compile(
    r">|\btee\b|\bsed\b[^|;&]*\s-[A-Za-z]*i|\bperl\b[^|;&]*\s-[A-Za-z]*i|"
    r"\b(?:rm|mv|cp|touch|truncate|dd|ln|chmod|chown|install)\b"
)
GIT_CONFIG = re.compile(r"\bgit\b(?:\s+-\S+(?:\s+\S+)?)*\s+config\b(.*)")
GIT_CONFIG_READ = re.compile(r"--(?:get|get-all|get-regexp|list|show-origin|show-scope)\b|\s-l\b")
GIT_CONFIG_WRITE_FLAG = re.compile(
    r"--(?:unset|unset-all|add|replace-all|edit|rename-section|remove-section)\b|\s-e\b"
)
GIT_CONFIG_OUTSIDE =re.compile(r"--(?:global|system)\b")


def git_config_writes(args):
    """True, если `git config <args>` меняет конфиг репозитория."""
    if GIT_CONFIG_OUTSIDE.search(args):
        return False
    if GIT_CONFIG_WRITE_FLAG.search(args):
        return True
    if GIT_CONFIG_READ.search(args):
        return False
    positional = [t for t in re.split(r"[\s;|&]+", args) if t and not t.startswith("-")]
    return len(positional) >= 2  # ключ и значение; один ключ только читается


def verdict(command):
    """Возвращает причину блокировки или None."""
    if ENV_FILE.search(command):
        return "команды с файлами .env запрещены: там секреты"

    cleaned = NOISE.sub(" ", command)

    m = GIT_CONFIG.search(cleaned)
    if m and git_config_writes(m.group(1)):
        return "git config меняет .git/config; правь конфиг репозитория вручную"

    touches_protected = GIT_DIR.search(cleaned) or LOCK_FILE.search(cleaned)
    if touches_protected and WRITE.search(cleaned):
        return "запись в .git/ или lock-файлы запрещена"
    return None


def main():
    data = json.load(sys.stdin)
    command = data.get("tool_input", {}).get("command", "")
    why = verdict(command) if command else None
    if why:
        print(f"Заблокировано: {why}.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
