#!/usr/bin/env python3
"""Cas d'essai du hook Config/claude/hooks/actions-reservees.py.

Usage : python3 scripts/test-hook-actions-reservees.py
"""
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "Config" / "claude" / "hooks" / "actions-reservees.py"

BLOQUES = [
    ("Bash", "git push origin main", ""),
    ("Bash", "git push -u origin HEAD:main", ""),
    ("Bash", "git push --force origin feature/x", ""),
    ("Bash", "git push origin +feature/x", ""),
    ("Bash", "npm test && gh pr merge 12 --squash", ""),
    ("Bash", "vercel deploy --prod", ""),
    ("Bash", "eas submit -p ios", ""),
    ("Bash", "kubectl apply -f k8s/", ""),
    ("Bash", "terraform apply -auto-approve", ""),
    ("Bash", "php artisan migrate:fresh --seed", ""),
    ("Bash", "php artisan migrate --force", ""),
    ("Bash", "cat .env", ""),
    ("Bash", "grep DB_PASSWORD .env.production", ""),
    ("Read", "/projet/.env", ""),
    ("Edit", "/projet/config/certs/server.key", ""),
    ("Bash", "echo test > app/Foo.php", "code-reviewer"),
    ("Bash", "sed -i 's/a/b/' app/Foo.php", "security-auditor"),
    ("Bash", "./vendor/bin/pint", "code-reviewer"),
    ("Bash", "git commit -am wip", "quality-gatekeeper"),
    ("Bash", "composer require foo/bar", "code-reviewer"),
    ("Bash", "cat > app/Probe.php <<'EOF'\n<?php echo 1;\nEOF", "security-auditor"),
    ("Bash", "bash <<'EOF'\nrm -rf app\nEOF", "code-reviewer"),
    ("Bash", "php artisan make:test ProbeTest", "quality-gatekeeper"),
    ("Bash", "npx eslint --fix src", "code-reviewer"),
]

PERMIS = [
    ("Bash", "git push -u origin feature/notes", ""),
    ("Bash", "git push --force-with-lease origin feature/notes", ""),
    ("Bash", "gh pr create --fill", ""),
    ("Bash", "cp .env.example .env && php artisan key:generate", ""),
    ("Bash", "cat .env.example", ""),
    ("Bash", "php artisan migrate:fresh --env=testing", ""),
    ("Bash", "php artisan migrate", ""),
    ("Bash", "php artisan test 2>&1 | tail -20", "code-reviewer"),
    ("Bash", "./vendor/bin/pint --test", "code-reviewer"),
    ("Bash", "git diff main...HEAD > /dev/null", "code-reviewer"),
    ("Bash", "php -r 'echo [1 => 2][1];'", "quality-gatekeeper"),
    ("Bash", "echo ok > app/Foo.php", "laravel-implementer"),
    ("Bash", "DB_CONNECTION=sqlite DB_DATABASE=:memory: php artisan migrate --force", ""),
    ("Bash", "mkdir -p /tmp/sonde && cat > /tmp/sonde/SondeTest.php <<'EOF'\n<?php\nrm ici n'est pas une commande;\n$a->b > 3;\nEOF", "security-auditor"),
    ("Bash", "ls vendor/bin | grep -i -E \"pint|phpstan\"", "code-reviewer"),
    ("Bash", "printf \"%s > %s\\n\" a b; rm /tmp/probe.php", "code-reviewer"),
    ("Bash", "git log --all -p 2>/dev/null | grep -nE \"secret\\s*=\" | head", "security-auditor"),
    ("Bash", "./vendor/bin/pint --test >/dev/null 2>&1; echo \"exit=$?\"", "quality-gatekeeper"),
    ("Bash", "php artisan migrate --env=testing", "quality-gatekeeper"),
    ("Bash", "DB_DATABASE=/tmp/m.sqlite bash -c 'touch /tmp/m.sqlite; php artisan migrate --force'", ""),
    ("Read", "/projet/.env.example", ""),
    ("Write", "/projet/app/Models/Note.php", ""),
]


def decision(outil: str, valeur: str, agent: str) -> int:
    cle = "command" if outil == "Bash" else "file_path"
    entree = {"tool_name": outil, "tool_input": {cle: valeur}, "agent_type": agent}
    return subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps(entree), text=True, capture_output=True
    ).returncode


def main() -> int:
    erreurs = [f"devait bloquer : {c}" for c in BLOQUES if decision(*c) != 2]
    erreurs += [f"devait permettre : {c}" for c in PERMIS if decision(*c) != 0]
    for erreur in erreurs:
        print(erreur)
    if erreurs:
        return 1
    print(f"{len(BLOQUES)} cas bloqués et {len(PERMIS)} cas permis, comme attendu.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
