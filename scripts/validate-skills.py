#!/usr/bin/env python3
"""Vérifie la forme des skills de Skills/ et les références des agents.

Contrôles :
  - en-tête YAML : `name` égal au nom du dossier, `description` non vide (< 1024 caractères) ;
  - sections du contrat présentes dans SKILL.md ;
  - noms de skills uniques ;
  - chaque skill cité par un agent ou un skill (champ `skills:` ou mention « skill `<nom>` »)
    est rédigé ou listé dans Skills/PREVUS.md ;
  - aucun skill de Skills/PREVUS.md n'est déjà rédigé.

Usage :
  python3 scripts/validate-skills.py            rapport rédigés / prévus / manquants
  python3 scripts/validate-skills.py --strict   échoue aussi si un skill cité n'est que prévu
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "Skills"
AGENTS_DIR = ROOT / "Agent"
PREVUS = SKILLS_DIR / "PREVUS.md"
MENTION = re.compile(r"skills? `([a-z0-9-]+)`")
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
    strict = "--strict" in sys.argv[1:]
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

    planned = set(re.findall(r"^- `([a-z0-9-]+)`", PREVUS.read_text(encoding="utf-8"), re.MULTILINE))
    for name in sorted(planned & skills.keys()):
        problems.append(f"Skills/PREVUS.md : « {name} » est déjà rédigé, retire-le de la liste")

    cited: dict[str, set[str]] = {}
    sources = [p for p in sorted(AGENTS_DIR.rglob("*.md")) if "_commun" not in p.parts]
    sources += sorted(SKILLS_DIR.rglob("SKILL.md"))
    for path in sources:
        text = path.read_text(encoding="utf-8")
        names = set(front_matter(text).get("skills", [])) | set(MENTION.findall(text))
        for name in names:
            cited.setdefault(name, set()).add(str(path.relative_to(ROOT)))

    waiting = {n: s for n, s in cited.items() if n not in skills and n in planned}
    missing = {n: s for n, s in cited.items() if n not in skills and n not in planned}
    for name, sources_ in sorted(missing.items()):
        problems.append(f"skill « {name} » ni rédigé ni prévu (cité par {', '.join(sorted(sources_))})")
    if strict:
        for name, sources_ in sorted(waiting.items()):
            problems.append(f"skill « {name} » seulement prévu (cité par {', '.join(sorted(sources_))})")

    written_cited = len([n for n in cited if n in skills])
    print(f"{len(skills)} skills rédigés ; skills cités : {written_cited} rédigés, {len(waiting)} prévus, {len(missing)} manquants.")
    if problems:
        print(*problems, sep="\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
