#!/usr/bin/env python3
"""Cas d'essai de scripts/install.py sur des projets jetables.

Usage : python3 scripts/test-install.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

INSTALL = Path(__file__).resolve().parent / "install.py"
echecs: list[str] = []


def lancer(*args: str, home: Path, cwd: Path) -> str:
    env = {**os.environ, "HOME": str(home)}
    resultat = subprocess.run([sys.executable, str(INSTALL), *args], cwd=cwd, env=env,
                              capture_output=True, text=True)
    return resultat.stdout + resultat.stderr


def verifier(condition: bool, cas: str) -> None:
    if not condition:
        echecs.append(cas)


def ecrire(chemin: Path, contenu: str) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8")


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    home = tmp / "home"
    home.mkdir()

    # Détection : Laravel avec Vite à la racine, Next.js dans un sous-dossier, Go non couvert.
    lara = tmp / "lara"
    ecrire(lara / "composer.json", '{"require": {"laravel/framework": "^11"}}')
    ecrire(lara / "package.json", '{"devDependencies": {"vite": "^5"}}')
    ecrire(lara / ".claude" / "agents" / "planner.md", "agent du projet\n")
    ecrire(lara / ".claude" / "settings.json", '{"permissions": {"deny": ["Bash(rm -rf:*)"]}}')
    ecrire(lara / "AGENTS.md", "# Règles du projet\n")
    sortie = lancer("--outil", "les-deux", home=home, cwd=lara)
    verifier("stacks détectées : laravel" in sortie, "détection de Laravel")
    verifier("non couvert" not in sortie, "le package.json de Vite n'est pas un projet à part")
    verifier((lara / ".claude" / "agents" / "laravel-implementer.md").exists(), "agent Laravel installé")
    verifier((lara / ".claude" / "agents" / "planner.md").read_text() == "agent du projet\n",
             "fichier du projet conservé sans --force")
    verifier((lara / ".codex" / "agents" / "laravel-implementer.toml").exists(), "agent Codex installé")
    verifier("Règles du projet" in (lara / "AGENTS.md").read_text(), "AGENTS.md du projet conservé")

    # Relance sans option : même installation, mise à jour sur place.
    sortie = lancer(home=home, cwd=lara)
    verifier("outil : les-deux, stacks : laravel" in sortie, "relance réutilise le manifeste")

    # Désinstallation : il ne reste que les fichiers du projet.
    lancer("--desinstaller", home=home, cwd=lara)
    restants = sorted(str(p.relative_to(lara)) for p in lara.rglob("*") if p.is_file())
    verifier(restants == [".claude/agents/planner.md", ".claude/settings.json", "AGENTS.md",
                          "composer.json", "package.json"], f"désinstallation propre ({restants})")
    reglages = json.loads((lara / ".claude" / "settings.json").read_text())
    verifier(reglages["permissions"]["deny"] == ["Bash(rm -rf:*)"] and "hooks" not in reglages,
             "réglages du projet rendus")
    verifier((lara / "AGENTS.md").read_text().strip() == "# Règles du projet", "bloc AGENTS.md retiré")

    mono = tmp / "mono"
    ecrire(mono / "apps" / "web" / "package.json", '{"dependencies": {"next": "15"}}')
    ecrire(mono / "services" / "outil" / "go.mod", "module outil\n")
    sortie = lancer("--outil", "claude", home=home, cwd=mono)
    verifier("stacks détectées : nextjs" in sortie, "détection dans un sous-dossier")
    verifier("non couvert : Go" in sortie, "langage non couvert signalé")

    # Langage : toutes les stacks TypeScript ; langage ou stack inconnus refusés.
    vide = tmp / "vide"
    vide.mkdir()
    sortie = lancer("--langage", "typescript", "--outil", "claude", home=home, cwd=vide)
    verifier("stacks : angular, nextjs, expo" in sortie, "--langage typescript")
    verifier("Langage non spécialisé" in lancer("--langage", "python", home=home, cwd=vide), "langage refusé")
    verifier("Stack inconnue" in lancer("--stack", "django", home=home, cwd=vide), "stack refusée")

    # Global : ~/.claude et ~/.codex, sans toucher au config.toml de l'utilisateur.
    ecrire(home / ".codex" / "config.toml", 'model = "perso"\n')
    sortie = lancer("--global", "--outil", "les-deux", home=home, cwd=vide)
    verifier("25 agents" in sortie, "global : toutes les stacks")
    verifier((home / ".claude" / "agents" / "expo-mobile-implementer.md").exists(), "global : agents Claude")
    verifier((home / ".agents" / "skills" / "laravel" / "SKILL.md").exists(), "global : skills Codex")
    verifier("~/.codex/agents/" in (home / ".codex" / "AGENTS.md").read_text(), "global : chemins Codex")
    verifier('$HOME' in (home / ".claude" / "settings.json").read_text(), "global : chemin du hook")
    verifier((home / ".codex" / "config.toml").read_text() == 'model = "perso"\n', "global : config.toml intact")
    lancer("--global", "--desinstaller", home=home, cwd=vide)
    verifier(sorted(str(p.relative_to(home)) for p in home.rglob("*") if p.is_file()) == [".codex/config.toml"],
             "global : désinstallation propre")

for cas in echecs:
    print(f"ÉCHEC : {cas}")
print(f"{'Échec' if echecs else 'Tous les cas passent'} ({len(echecs)} échec(s)).")
sys.exit(1 if echecs else 0)
