#!/usr/bin/env python3
"""Synchronise les agents avec les principes partagés et génère la version Codex.

Un agent ne lit que son propre fichier : les principes partagés doivent donc
y être recopiés. Ils sont maintenus à un seul endroit et ce script :
  1. recopie Agent/_commun/principes-communs.md dans chaque agent ;
  2. recopie Agent/_commun/principes-code.md dans les agents qui modifient
     du code (CODE_AGENTS) et le retire des autres ;
  3. génère Codex/agents/<nom>.toml (agents personnalisés Codex) et
     Codex/AGENTS.md (instructions de la session principale Codex).

Usage :
  python3 scripts/sync-agents.py          met à jour les agents et Codex/
  python3 scripts/sync-agents.py --check  échoue si un fichier n'est pas à jour
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "Agent"
COMMUN = AGENTS_DIR / "_commun"
CODEX_DIR = ROOT / "Codex"
CODEX_AGENTS_MD_MAX_BYTES = 32 * 1024  # project_doc_max_bytes par défaut de Codex

CODE_AGENTS = {
    "implementer",
    "laravel-implementer",
    "symfony-implementer",
    "spring-boot-implementer",
    "angular-implementer",
    "nextjs-implementer",
    "expo-mobile-implementer",
    "debugger",
    "refactorer",
    "performance-optimizer",
    "data-modeler",
    "test-engineer",
    "e2e-validator",
    "scaffolder",
    "devops-engineer",
}

BLOCKS = [
    ("PRINCIPES-COMMUNS", "principes-communs.md"),
    ("PRINCIPES-CODE", "principes-code.md"),
]


def markers(tag: str, source: str) -> tuple[str, str]:
    start = f"<!-- {tag}:DEBUT — généré depuis Agent/_commun/{source}, ne pas modifier ici -->"
    return start, f"<!-- {tag}:FIN -->"


def strip_block(text: str, tag: str, source: str) -> str:
    start, end = markers(tag, source)
    if start not in text or end not in text:
        return text
    before, rest = text.split(start, 1)
    after = rest.split(end, 1)[1].lstrip("\n")
    return before.rstrip("\n") + "\n" + (("\n" + after) if after else "")


def render_agent(text: str, name: str) -> str:
    for tag, source in BLOCKS:
        text = strip_block(text, tag, source)
    text = text.rstrip("\n") + "\n"
    for tag, source in BLOCKS:
        if tag == "PRINCIPES-CODE" and name not in CODE_AGENTS:
            continue
        start, end = markers(tag, source)
        block = (COMMUN / source).read_text(encoding="utf-8").strip()
        text += f"\n{start}\n{block}\n{end}\n"
    return text


def parse_agent(text: str) -> tuple[dict, str]:
    """Lit l'en-tête YAML simple des agents (clés scalaires et listes « - »)."""
    _, header, body = text.split("---\n", 2)
    meta: dict = {}
    key = None
    for line in header.splitlines():
        if line.startswith("  - ") and key:
            meta.setdefault(key, []).append(line[4:].strip())
        elif ":" in line:
            key, value = (part.strip() for part in line.split(":", 1))
            if value:
                meta[key] = value
    return meta, body.lstrip("\n")


def render_codex_agent(meta: dict, body: str) -> str:
    if "'''" in body:
        raise ValueError(f"{meta['name']} : ''' interdit dans le corps (chaîne TOML littérale)")
    return (
        "# Généré par scripts/sync-agents.py depuis Agent/, ne pas modifier ici.\n"
        f"name = {json.dumps(meta['name'], ensure_ascii=False)}\n"
        f"description = {json.dumps(meta['description'], ensure_ascii=False)}\n"
        f"developer_instructions = '''\n{body}'''\n"
    )


def render_codex_agents_md(agents: list[tuple[dict, Path]]) -> str:
    rows = "\n".join(
        f"| `{meta['name']}` | {meta['description']} |" for meta, _ in agents
    )
    communs = (COMMUN / "principes-communs.md").read_text(encoding="utf-8").strip()
    code = (COMMUN / "principes-code.md").read_text(encoding="utf-8").strip()
    return f"""<!-- Généré par scripts/sync-agents.py depuis Agent/, ne pas modifier ici. -->
# Instructions du projet

Au début de chaque session, lis `docs/PROJECT.md` et les dernières entrées de `docs/journal/` s'ils existent.

## Travail avec les agents spécialisés

Les agents du projet sont définis dans `.codex/agents/`. Tu es la session principale : tu parles à l'utilisateur, les agents ne lui parlent pas.

- **Petite tâche dans une seule phase** (corriger un bug précis, coder une tâche du plan) : lance l'agent de la phase avec un brief complet, ou fais-la toi-même en appliquant les principes ci-dessous.
- **Demande qui traverse plusieurs phases** (nouveau projet, nouvelle fonctionnalité de bout en bout) : lis `.codex/agents/orchestrator.toml` et applique toi-même sa procédure ; tu lances les autres agents comme sous-agents.
- **Contrôle indépendant** : un agent de contrôle (`code-reviewer`, `security-auditor`, `e2e-validator`, `quality-gatekeeper`) reçoit la spec et le livrable, jamais l'avis de l'agent qui a produit le travail.
- Quand un agent termine par une « Question pour l'utilisateur », pose-la à l'utilisateur, puis relance l'agent avec la réponse.

| Agent | Quand l'utiliser |
|-------|------------------|
{rows}

{communs}

{code}
"""


def main() -> int:
    check = "--check" in sys.argv[1:]
    paths = [p for p in sorted(AGENTS_DIR.rglob("*.md")) if "_commun" not in p.parts]
    agents = []
    expected: dict[Path, str] = {}
    for path in paths:
        current = path.read_text(encoding="utf-8")
        meta, _ = parse_agent(current)
        updated = render_agent(current, meta["name"])
        expected[path] = updated
        _, body = parse_agent(updated)
        agents.append((meta, path))
        expected[CODEX_DIR / "agents" / f"{meta['name']}.toml"] = render_codex_agent(meta, body)

    unknown = CODE_AGENTS - {meta["name"] for meta, _ in agents}
    if unknown:
        print("CODE_AGENTS cite des agents inexistants :", *sorted(unknown))
        return 1

    agents_md = render_codex_agents_md(agents)
    size = len(agents_md.encode("utf-8"))
    if size > CODEX_AGENTS_MD_MAX_BYTES:
        print(f"Codex/AGENTS.md fait {size} octets, au-delà de la limite de Codex ({CODEX_AGENTS_MD_MAX_BYTES}).")
        return 1
    expected[CODEX_DIR / "AGENTS.md"] = agents_md

    stale_codex = [
        p for p in sorted((CODEX_DIR / "agents").glob("*.toml")) if p not in expected
    ] if (CODEX_DIR / "agents").exists() else []

    stale = [
        p for p, content in expected.items()
        if not p.exists() or p.read_text(encoding="utf-8") != content
    ] + stale_codex

    if check:
        if stale:
            print("Fichiers à resynchroniser :", *(p.relative_to(ROOT) for p in stale), sep="\n  ")
            return 1
        print(f"{len(agents)} agents et version Codex à jour.")
        return 0

    for path in stale:
        if path in stale_codex:
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected[path], encoding="utf-8")
    print(f"{len(agents)} agents, {len(stale)} fichiers mis à jour.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
