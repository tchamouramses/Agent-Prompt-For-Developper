#!/usr/bin/env python3
"""Vérifie la forme des skills de Skills/ et les références des agents.

Contrôles :
  - en-tête YAML : `name` égal au nom du dossier, `description` non vide (< 1024 caractères) ;
  - sections du contrat présentes dans SKILL.md ;
  - noms de skills uniques ;
  - chaque skill cité dans le champ `skills:` d'un agent existe ou figure au catalogue.

Usage : python3 scripts/validate-skills.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "Skills"
AGENTS_DIR = ROOT / "Agent"
CATALOGUE = ROOT / "docs" / "catalogue.md"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DESCRIPTION_MAX = 1024
SECTIONS = [
    "Quand l'utiliser",
    "Ce que l'agent rate sans ce skill",
    "Entrées",
    "Procédure",
    "Livrable",
    "Vérifications",
    "Limites",
    "En cas de blocage",
]


def front_matter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    header = text.split("---\n", 2)[1]
    meta: dict = {}
    key = None
    for line in header.splitlines():
        if line.startswith("  - ") and key:
            meta.setdefault(key, []).append(line[4:].strip())
        elif ":" in line:
            key, value = (part.strip() for part in line.split(":", 1))
            if value:
                meta[key] = value
    return meta


def check_skill(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    meta = front_matter(text)
    folder = path.parent.name
    errors = []
    name = meta.get("name", "")
    if name != folder:
        errors.append(f"name « {name} » différent du dossier « {folder} »")
    if not NAME_PATTERN.match(folder):
        errors.append("nom de dossier hors format (minuscules, chiffres, tirets)")
    description = meta.get("description", "")
    if not description:
        errors.append("description absente")
    elif len(description) >= DESCRIPTION_MAX:
        errors.append(f"description de {len(description)} caractères (max {DESCRIPTION_MAX - 1})")
    prose = re.sub(r"^```.*?^```", "", text, flags=re.MULTILINE | re.DOTALL)
    headings = re.findall(r"^## (.+)$", prose, re.MULTILINE)
    for section in SECTIONS:
        if not any(h.startswith(section) for h in headings):
            errors.append(f"section manquante : « {section} »")
    return errors


def main() -> int:
    problems: list[str] = []
    skills: dict[str, Path] = {}
    for path in sorted(SKILLS_DIR.rglob("SKILL.md")):
        rel = path.relative_to(ROOT)
        for error in check_skill(path):
            problems.append(f"{rel} : {error}")
        name = path.parent.name
        if name in skills:
            problems.append(f"{rel} : nom déjà utilisé par {skills[name].relative_to(ROOT)}")
        skills[name] = path

    planned = set(re.findall(r"`([a-z0-9-]+)`", CATALOGUE.read_text(encoding="utf-8")))
    for path in sorted(AGENTS_DIR.rglob("*.md")):
        if "_commun" in path.parts:
            continue
        for skill in front_matter(path.read_text(encoding="utf-8")).get("skills", []):
            if skill not in skills and skill not in planned:
                problems.append(f"{path.relative_to(ROOT)} : skill « {skill} » ni rédigé ni prévu au catalogue")

    if problems:
        print(*problems, sep="\n")
        return 1
    print(f"{len(skills)} skills valides, références des agents correctes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
