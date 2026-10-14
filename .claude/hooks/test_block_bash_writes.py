import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from block_bash_writes import verdict  # noqa: E402

BLOCKED = [
    "echo SECRET=1 >> .env",
    "cat .env",
    "grep TOKEN .env.local",
    "source ./.env",
    'echo "[user]" >> .git/config',
    "sed -i '' 's/a/b/' .git/config",
    "rm .git/HEAD",
    "git config --unset user.name",
    "git config user.name test",
    "git config --local user.email a@b.c",
    "echo '{}' > package-lock.json",
    "rm poetry.lock",
    "mv Cargo.lock /tmp/x",
    "touch yarn.lock",
    "printf x | tee .git/hooks/pre-commit",
]

ALLOWED = [
    "git status",
    "git log --oneline -5",
    "cat .git/config",
    "git config --get user.name",
    "git config --list",
    "git config user.name",
    "git config --local remote.origin.url",
    "git config --global user.name someone",
    "cat package-lock.json",
    "ls -la .gitignore",
    "echo node_modules/ >> .gitignore",
    "./mvnw test 2>&1 | tail -20",
    "cat README.md 2>/dev/null",
    "git commit -m 'update env docs'",
    "ls .github",
    "cat .envrc.md",
]


class VerdictTest(unittest.TestCase):
    def test_blocks_dangerous_commands(self):
        for cmd in BLOCKED:
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(verdict(cmd), f"должна блокироваться: {cmd}")

    def test_allows_safe_commands(self):
        for cmd in ALLOWED:
            with self.subTest(cmd=cmd):
                self.assertIsNone(verdict(cmd), f"не должна блокироваться: {cmd}")


if __name__ == "__main__":
    unittest.main()
