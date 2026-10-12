#!/usr/bin/env python3
"""Installe les agents, les skills et les garde-fous de cette bibliothèque dans un projet.

Installe les agents globaux, l'agent d'implémentation de chaque stack choisie, tous les
skills rédigés qu'ils citent (directement ou par un autre skill), et les réglages qui
imposent les actions réservées. Un fichier existant du projet n'est jamais écrasé sans
--force, sauf les réglages Claude Code, fusionnés.

Usage :
  python3 scripts/install.py <dossier-du-projet> --stack laravel[,nextjs] [--outil claude|codex|les-deux] [--force]

Stacks : laravel, symfony, spring-boot, angular, nextjs, expo, aucune.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STACKS = {
    "laravel": "PHP/laravel-implementer.md",
    "symfony": "PHP/symfony-implementer.md",
    "spring-boot": "Java/spring-boot-implementer.md",
    "angular": "TypeScript/angular-implementer.md",
    "nextjs": "TypeScript/nextjs-implementer.md",
    "expo": "TypeScript/expo-mobile-implementer.md",
}
MENTION = re.compile(r"skills? `([a-z0-9-]+)`")


def skills_rediges() -> dict[str, Path]:
    return {p.parent.name: p.parent for p in ROOT.glob("Skills/*/*/SKILL.md")}


def cites(texte: str) -> set[str]:
    noms = set(MENTION.findall(texte))
    entete = texte.split("---\n", 2)[1] if texte.startswith("---\n") else ""
    noms |= set(re.findall(r"^  - ([a-z0-9-]+)$", entete, re.MULTILINE))
    return noms


def agents_choisis(stacks: list[str]) -> list[Path]:
    agents = sorted((ROOT / "Agent" / "Global").glob("*.md"))
    agents += [ROOT / "Agent" / STACKS[s] for s in stacks]
    return agents


def fermeture_skills(agents: list[Path], rediges: dict[str, Path]) -> tuple[set[str], set[str]]:
    a_voir = set().union(*(cites(a.read_text(encoding="utf-8")) for a in agents))
    retenus: set[str] = set()
    absents: set[str] = set()
    while a_voir:
        nom = a_voir.pop()
        if nom in retenus or nom in absents:
            continue
        if nom not in rediges:
            absents.add(nom)
            continue
        retenus.add(nom)
        a_voir |= cites((rediges[nom] / "SKILL.md").read_text(encoding="utf-8"))
    return retenus, absents


def copier(source: Path, cible: Path, force: bool, journal: list[str]) -> None:
    if cible.exists() and not force:
        journal.append(f"conservé (existe déjà) : {cible}")
        return
    cible.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.rmtree(cible, ignore_errors=True)
        shutil.copytree(source, cible)
    else:
        shutil.copy2(source, cible)
    journal.append(f"installé : {cible}")


def fusionner_reglages_claude(projet: Path, journal: list[str]) -> None:
    modele = json.loads((ROOT / "Config" / "claude" / "settings.json").read_text(encoding="utf-8"))
    cible = projet / ".claude" / "settings.json"
    actuel = json.loads(cible.read_text(encoding="utf-8")) if cible.exists() else {}
    refus = actuel.setdefault("permissions", {}).setdefault("deny", [])
    refus.extend(r for r in modele["permissions"]["deny"] if r not in refus)
    pre = actuel.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if not any("actions-reservees.py" in json.dumps(h) for h in pre):
        pre.extend(modele["hooks"]["PreToolUse"])
    actuel.setdefault("$schema", modele["$schema"])
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(json.dumps(actuel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    journal.append(f"fusionné : {cible}")


def installer_claude(projet, agents, skills, rediges, force, journal) -> None:
    for agent in agents:
        copier(agent, projet / ".claude" / "agents" / agent.name, force, journal)
    for nom in sorted(skills):
        copier(rediges[nom], projet / ".claude" / "skills" / nom, force, journal)
    copier(ROOT / "Config" / "claude" / "hooks" / "actions-reservees.py",
           projet / ".claude" / "hooks" / "actions-reservees.py", True, journal)
    fusionner_reglages_claude(projet, journal)


def installer_codex(projet, agents, skills, rediges, force, journal) -> None:
    copier(ROOT / "Codex" / "AGENTS.md", projet / "AGENTS.md", force, journal)
    for agent in agents:
        toml = ROOT / "Codex" / "agents" / f"{agent.stem}.toml"
        copier(toml, projet / ".codex" / "agents" / toml.name, force, journal)
    for nom in sorted(skills):
        copier(rediges[nom], projet / ".agents" / "skills" / nom, force, journal)
    copier(ROOT / "Config" / "codex" / "config.toml", projet / ".codex" / "config.toml", force, journal)
    copier(ROOT / "Config" / "codex" / "rules" / "actions-reservees.rules",
           projet / ".codex" / "rules" / "actions-reservees.rules", True, journal)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("projet", type=Path)
    parser.add_argument("--stack", required=True, help="stacks séparées par des virgules, ou « aucune »")
    parser.add_argument("--outil", choices=["claude", "codex", "les-deux"], default="claude")
    parser.add_argument("--force", action="store_true", help="remplace les fichiers déjà présents")
    args = parser.parse_args()

    stacks = [] if args.stack == "aucune" else [s.strip() for s in args.stack.split(",")]
    inconnues = [s for s in stacks if s not in STACKS]
    if inconnues or not args.projet.is_dir():
        print(f"Stack inconnue : {', '.join(inconnues)}" if inconnues else f"Dossier introuvable : {args.projet}")
        return 1

    rediges = skills_rediges()
    agents = agents_choisis(stacks)
    skills, absents = fermeture_skills(agents, rediges)
    journal: list[str] = []
    if args.outil in ("claude", "les-deux"):
        installer_claude(args.projet, agents, skills, rediges, args.force, journal)
    if args.outil in ("codex", "les-deux"):
        installer_codex(args.projet, agents, skills, rediges, args.force, journal)

    print(*journal, sep="\n")
    print(f"\n{len(agents)} agents et {len(skills)} skills installés pour : {', '.join(stacks) or 'aucune stack'}.")
    if absents:
        print(f"Skills cités mais pas encore rédigés ({len(absents)}), signalés par les agents s'ils en ont besoin :")
        print("  " + ", ".join(sorted(absents)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
