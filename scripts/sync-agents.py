#!/usr/bin/env python3
"""Injecte Agent/_commun/principes-communs.md dans chaque fichier d'agent.

Un agent ne lit que son propre fichier : les principes communs doivent donc
y être recopiés. Ils sont maintenus à un seul endroit et ce script les
recopie entre deux marqueurs (ajoutés en fin de fichier s'ils manquent).

Usage :
  python3 scripts/sync-agents.py          met à jour les agents
  python3 scripts/sync-agents.py --check  échoue si un agent n'est pas à jour
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "Agent" / "_commun" / "principes-communs.md"
START = "<!-- PRINCIPES-COMMUNS:DEBUT — généré depuis Agent/_commun/principes-communs.md, ne pas modifier ici -->"
END = "<!-- PRINCIPES-COMMUNS:FIN -->"


def render(agent_text: str, block: str) -> str:
    section = f"{START}\n{block.strip()}\n{END}\n"
    if START in agent_text and END in agent_text:
        before = agent_text.split(START, 1)[0]
        after = agent_text.split(END, 1)[1].lstrip("\n")
        return before + section + after
    return agent_text.rstrip("\n") + "\n\n" + section


def main() -> int:
    check = "--check" in sys.argv[1:]
    block = SOURCE.read_text(encoding="utf-8")
    agents = [p for p in sorted((ROOT / "Agent").rglob("*.md")) if "_commun" not in p.parts]
    stale = []
    for path in agents:
        current = path.read_text(encoding="utf-8")
        updated = render(current, block)
        if updated != current:
            stale.append(path.relative_to(ROOT))
            if not check:
                path.write_text(updated, encoding="utf-8")
    if check and stale:
        print("Agents à resynchroniser :", *stale, sep="\n  ")
        return 1
    print(f"{len(agents)} agents, {'tous à jour' if check else f'{len(stale)} mis à jour'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
