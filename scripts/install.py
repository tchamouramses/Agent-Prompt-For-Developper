#!/usr/bin/env python3
"""Installe les agents, les skills et les garde-fous de cette bibliothèque dans un projet ou pour tous les projets.

Installe les agents globaux, l'agent d'implémentation de chaque stack retenue, tous les skills
rédigés qu'ils citent (directement ou par un autre skill), et les réglages qui imposent les
actions réservées. Pour Claude Code, il autorise aussi sans confirmation les commandes de
développement générales puis celles des stacks retenues (Config/claude/autorisations-stacks.json),
pour que les agents avancent sans attendre l'humain ; les refus et le hook passent toujours avant. Les stacks sont détectées dans le projet si aucune n'est donnée.

Un manifeste (.bibliotheque-agents.json) liste ce qui a été installé : relancer la commande met
à jour ces fichiers et retire ceux devenus inutiles ; --desinstaller les retire tous. Un fichier
du projet qui n'a pas été installé par ce script n'est jamais écrasé sans --force.

Usage :
  python3 scripts/install.py [dossier-du-projet] [--stack auto|laravel,nextjs|toutes|aucune]
                             [--langage php,java,typescript] [--outil auto|claude|codex|les-deux]
                             [--global] [--force] [--desinstaller]

Exemples :
  python3 scripts/install.py                            projet courant, stacks et outils détectés
  python3 scripts/install.py ~/mon-api --stack laravel  stack imposée
  python3 scripts/install.py --langage typescript       agents Angular, Next.js et Expo
  python3 scripts/install.py --global                   ~/.claude et ~/.codex, toutes les stacks
  python3 scripts/install.py --desinstaller             retire ce qui a été installé ici
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTE = ".bibliotheque-agents.json"
STACKS = {
    "laravel": "PHP/laravel-implementer.md",
    "symfony": "PHP/symfony-implementer.md",
    "spring-boot": "Java/spring-boot-implementer.md",
    "angular": "TypeScript/angular-implementer.md",
    "nextjs": "TypeScript/nextjs-implementer.md",
    "expo": "TypeScript/expo-mobile-implementer.md",
}
LANGAGES = {
    "php": ["laravel", "symfony"],
    "java": ["spring-boot"],
    "typescript": ["angular", "nextjs", "expo"],
}
NON_COUVERTS = {
    "go.mod": "Go", "pyproject.toml": "Python", "requirements.txt": "Python", "Cargo.toml": "Rust",
    "pubspec.yaml": "Dart/Flutter", "Gemfile": "Ruby", "mix.exs": "Elixir",
}
IGNORES = {"node_modules", "vendor", ".git", "dist", "build", "target", ".next", ".expo", "storage"}
MENTION = re.compile(r"skills? `([a-z0-9-]+)`")


# --- Choix des agents et skills -------------------------------------------------------------

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


# --- Détection ------------------------------------------------------------------------------

def fichiers_marqueurs(projet: Path, profondeur: int = 2):
    """Parcourt la racine et les sous-dossiers jusqu'à `profondeur` (apps/web, packages/api…)."""
    dossiers = [projet]
    for _ in range(profondeur + 1):
        suivants = []
        for dossier in dossiers:
            try:
                enfants = list(dossier.iterdir())
            except OSError:
                continue
            for enfant in enfants:
                if enfant.is_file():
                    yield enfant
                elif enfant.is_dir() and enfant.name not in IGNORES and not enfant.name.startswith("."):
                    suivants.append(enfant)
        dossiers = suivants


def lire_json(chemin: Path) -> dict:
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def detecter(projet: Path) -> tuple[list[str], dict[str, str]]:
    """Retourne les stacks couvertes trouvées et les langages vus sans stack couverte (langage -> fichier)."""
    stacks: set[str] = set()
    autres: dict[str, tuple[str, Path]] = {}
    couverts: set[Path] = set()
    for fichier in fichiers_marqueurs(projet):
        relatif = str(fichier.relative_to(projet))
        if fichier.name == "composer.json":
            paquets = {**lire_json(fichier).get("require", {}), **lire_json(fichier).get("require-dev", {})}
            if "laravel/framework" in paquets:
                stacks.add("laravel")
                couverts.add(fichier.parent)
            elif "symfony/framework-bundle" in paquets:
                stacks.add("symfony")
                couverts.add(fichier.parent)
            else:
                autres.setdefault("PHP sans Laravel ni Symfony", (relatif, fichier.parent))
        elif fichier.name in ("pom.xml", "build.gradle", "build.gradle.kts"):
            if "spring-boot" in fichier.read_text(encoding="utf-8", errors="ignore"):
                stacks.add("spring-boot")
                couverts.add(fichier.parent)
            else:
                autres.setdefault("Java ou Kotlin sans Spring Boot", (relatif, fichier.parent))
        elif fichier.name == "package.json":
            donnees = lire_json(fichier)
            paquets = {**donnees.get("dependencies", {}), **donnees.get("devDependencies", {})}
            if "expo" in paquets:
                stacks.add("expo")
                couverts.add(fichier.parent)
            elif "next" in paquets:
                stacks.add("nextjs")
                couverts.add(fichier.parent)
            elif "@angular/core" in paquets:
                stacks.add("angular")
                couverts.add(fichier.parent)
            elif paquets:
                autres.setdefault("JavaScript/TypeScript sans Angular, Next.js ni Expo", (relatif, fichier.parent))
        elif fichier.name in NON_COUVERTS:
            autres.setdefault(NON_COUVERTS[fichier.name], (relatif, fichier.parent))
        elif fichier.suffix == ".csproj":
            autres.setdefault(".NET", (relatif, fichier.parent))
    # Un package.json à côté d'un composer.json Laravel (Vite) n'est pas un projet JavaScript à part.
    return sorted(stacks), {l: rel for l, (rel, dossier) in autres.items() if dossier not in couverts}


def outils_detectes() -> str:
    claude, codex = shutil.which("claude"), shutil.which("codex")
    if claude and codex:
        return "les-deux"
    return "codex" if codex and not claude else "claude"


# --- Écriture -------------------------------------------------------------------------------

class Installation:
    """Copie les fichiers et tient le manifeste de ce qui appartient à la bibliothèque."""

    def __init__(self, base: Path, force: bool, ancien: dict):
        self.base = base
        self.force = force
        self.anciens = set(ancien.get("fichiers", []))
        self.fichiers: list[str] = []
        self.refus_ajoutes: list[str] = list(ancien.get("refus_ajoutes", []))
        self.autorisations_ajoutees: list[str] = list(ancien.get("autorisations_ajoutees", []))
        self.journal: list[str] = []

    def rel(self, cible: Path) -> str:
        return str(cible.relative_to(self.base))

    def copier(self, source: Path, cible: Path, toujours: bool = False) -> None:
        rel = self.rel(cible)
        if cible.exists() and not (self.force or toujours or rel in self.anciens):
            self.journal.append(f"conservé (existe déjà, pas installé par ce script) : {cible}")
            return
        cible.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.rmtree(cible, ignore_errors=True)
            shutil.copytree(source, cible)
        else:
            shutil.copy2(source, cible)
        self.fichiers.append(rel)
        self.journal.append(f"{'mis à jour' if rel in self.anciens else 'installé'} : {cible}")

    def ecrire(self, cible: Path, contenu: str) -> None:
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(contenu, encoding="utf-8")

    def retirer_obsoletes(self) -> None:
        for rel in sorted(self.anciens - set(self.fichiers)):
            supprimer(self.base / rel, self.journal)


def supprimer(chemin: Path, journal: list[str]) -> None:
    if chemin.is_dir():
        shutil.rmtree(chemin)
    elif chemin.exists():
        chemin.unlink()
    else:
        return
    journal.append(f"retiré : {chemin}")


def commande_hook(global_: bool) -> str:
    racine = '"$HOME"' if global_ else '"$CLAUDE_PROJECT_DIR"'
    return f"python3 {racine}/.claude/hooks/actions-reservees.py"


def autorisations(modele: dict, stacks: list[str]) -> list[str]:
    """Commandes générales de settings.json, puis celles des stacks retenues (autorisations-stacks.json)."""
    par_stack = lire_json(ROOT / "Config" / "claude" / "autorisations-stacks.json")
    regles = list(modele["permissions"]["allow"])
    for stack in stacks:
        regles += [r for r in par_stack.get(stack, []) if r not in regles]
    return regles


def fusionner_reglages_claude(inst: Installation, global_: bool, stacks: list[str]) -> None:
    modele = json.loads((ROOT / "Config" / "claude" / "settings.json").read_text(encoding="utf-8"))
    cible = inst.base / ".claude" / "settings.json"
    actuel = lire_json(cible) if cible.exists() else {}
    permissions = actuel.setdefault("permissions", {})
    refus = permissions.setdefault("deny", [])
    for regle in modele["permissions"]["deny"]:
        if regle not in refus:
            refus.append(regle)
            inst.refus_ajoutes.append(regle)
    # Les autorisations suivent les stacks : celles d'une stack retirée disparaissent à la relance.
    voulues = autorisations(modele, stacks)
    permis = [r for r in permissions.get("allow", []) if r not in inst.autorisations_ajoutees or r in voulues]
    inst.autorisations_ajoutees = [r for r in inst.autorisations_ajoutees if r in voulues]
    for regle in voulues:
        if regle not in permis:
            permis.append(regle)
            inst.autorisations_ajoutees.append(regle)
    permissions["allow"] = permis
    pre = actuel.setdefault("hooks", {}).setdefault("PreToolUse", [])
    pre[:] = [h for h in pre if "actions-reservees.py" not in json.dumps(h)]
    hook = json.loads(json.dumps(modele["hooks"]["PreToolUse"]))
    for entree in hook:
        for h in entree["hooks"]:
            h["command"] = commande_hook(global_)
    pre.extend(hook)
    actuel.setdefault("$schema", modele["$schema"])
    inst.ecrire(cible, json.dumps(actuel, ensure_ascii=False, indent=2) + "\n")
    inst.journal.append(f"fusionné : {cible}")


def retirer_reglages_claude(base: Path, refus_ajoutes: list[str], autorisations_ajoutees: list[str],
                            journal: list[str]) -> None:
    cible = base / ".claude" / "settings.json"
    if not cible.exists():
        return
    actuel = lire_json(cible)
    permissions = actuel.get("permissions", {})
    if "deny" in permissions:
        permissions["deny"] = [r for r in permissions["deny"] if r not in refus_ajoutes]
    if "allow" in permissions:
        permissions["allow"] = [r for r in permissions["allow"] if r not in autorisations_ajoutees]
    pre = actuel.get("hooks", {}).get("PreToolUse")
    if pre is not None:
        actuel["hooks"]["PreToolUse"] = [h for h in pre if "actions-reservees.py" not in json.dumps(h)]
    for cle, enfant in (("permissions", "allow"), ("permissions", "deny"), ("hooks", "PreToolUse")):
        if actuel.get(cle, {}).get(enfant) == []:
            del actuel[cle][enfant]
        if actuel.get(cle) == {}:
            del actuel[cle]
    if set(actuel) <= {"$schema"}:
        supprimer(cible, journal)
        return
    cible.write_text(json.dumps(actuel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    journal.append(f"nettoyé : {cible}")


def retirer_dossiers_vides(base: Path) -> None:
    for racine in (base / ".claude", base / ".codex", base / ".agents"):
        if not racine.is_dir():
            continue
        for dossier in sorted((d for d in racine.rglob("*") if d.is_dir()), key=lambda d: -len(d.parts)) + [racine]:
            if not any(dossier.iterdir()):
                dossier.rmdir()


DEBUT_BLOC = "<!-- BIBLIOTHEQUE-AGENTS:DEBUT -->"
FIN_BLOC = "<!-- BIBLIOTHEQUE-AGENTS:FIN -->"


def remplacer_bloc(actuel: str, bloc: str) -> str:
    if DEBUT_BLOC in actuel and FIN_BLOC in actuel:
        avant, reste = actuel.split(DEBUT_BLOC, 1)
        apres = reste.split(FIN_BLOC, 1)[1].lstrip("\n")
        return (avant + bloc + apres) if bloc else (avant.rstrip() + "\n" + apres if avant.strip() else apres)
    if not bloc:
        return actuel
    return (actuel.rstrip() + "\n\n" if actuel.strip() else "") + bloc


def retirer_bloc_agents_md(base: Path, journal: list[str]) -> None:
    for agents_md in (base / "AGENTS.md", base / ".codex" / "AGENTS.md"):
        if agents_md.exists() and DEBUT_BLOC in agents_md.read_text(encoding="utf-8"):
            reste = remplacer_bloc(agents_md.read_text(encoding="utf-8"), "")
            if reste.strip():
                agents_md.write_text(reste, encoding="utf-8")
            else:
                agents_md.unlink()
            journal.append(f"bloc retiré : {agents_md}")


def fusionner_agents_md(inst: Installation, global_: bool) -> None:
    """Ajoute les instructions Codex entre marqueurs, sans effacer celles déjà présentes."""
    texte = (ROOT / "Codex" / "AGENTS.md").read_text(encoding="utf-8").strip()
    if global_:
        texte = texte.replace("`.codex/agents/", "`~/.codex/agents/")
    cible = inst.base / (".codex/AGENTS.md" if global_ else "AGENTS.md")
    actuel = cible.read_text(encoding="utf-8") if cible.exists() else ""
    nouveau = remplacer_bloc(actuel, f"{DEBUT_BLOC}\n{texte}\n{FIN_BLOC}\n")
    inst.ecrire(cible, nouveau)
    taille = len(nouveau.encode("utf-8"))
    inst.journal.append(f"fusionné : {cible} ({taille} octets)")
    if taille > 32 * 1024:
        inst.journal.append("attention : AGENTS.md dépasse 32 Kio, limite par défaut de Codex (project_doc_max_bytes)")


def installer_claude(inst, agents, skills, rediges, global_, stacks) -> None:
    for agent in agents:
        inst.copier(agent, inst.base / ".claude" / "agents" / agent.name)
    for nom in sorted(skills):
        inst.copier(rediges[nom], inst.base / ".claude" / "skills" / nom)
    inst.copier(ROOT / "Config" / "claude" / "hooks" / "actions-reservees.py",
                inst.base / ".claude" / "hooks" / "actions-reservees.py", toujours=True)
    fusionner_reglages_claude(inst, global_, stacks)


def installer_codex(inst, agents, skills, rediges, global_) -> None:
    fusionner_agents_md(inst, global_)
    for agent in agents:
        toml = ROOT / "Codex" / "agents" / f"{agent.stem}.toml"
        inst.copier(toml, inst.base / ".codex" / "agents" / toml.name)
    for nom in sorted(skills):
        inst.copier(rediges[nom], inst.base / ".agents" / "skills" / nom)
    if not global_:  # ~/.codex/config.toml appartient à l'utilisateur : on n'y touche pas.
        inst.copier(ROOT / "Config" / "codex" / "config.toml", inst.base / ".codex" / "config.toml")
    inst.copier(ROOT / "Config" / "codex" / "rules" / "actions-reservees.rules",
                inst.base / ".codex" / "rules" / "actions-reservees.rules", toujours=True)


# --- Commande -------------------------------------------------------------------------------

def choisir_stacks(args, projet: Path, precedent: dict) -> tuple[list[str], list[str], bool]:
    """Retourne les stacks retenues, les remarques à afficher et si le projet est encore sans code.

    `precedent` est le manifeste d'une installation que l'on relance sans option ; ses stacks sont
    gardées et complétées par celles détectées depuis (une application ajoutée au dépôt).
    """
    remarques: list[str] = []
    nouveau = False
    if args.stack == "aucune":
        stacks: list[str] = []
    elif args.stack == "toutes" or (args.stack == "auto" and args.global_ and not args.langage):
        stacks = list(STACKS)
    elif args.stack == "auto" and not args.langage:
        stacks, autres = detecter(projet)
        remarques.append(f"stacks détectées : {', '.join(stacks) or 'aucune'}")
        for langage, fichier in autres.items():
            remarques.append(f"non couvert : {langage} ({fichier}), agents génériques seulement")
        if precedent and not precedent.get("nouveau"):
            ajoutees = [s for s in stacks if s not in precedent.get("stacks", [])]
            stacks = sorted(set(stacks) | set(precedent.get("stacks", [])))
            if ajoutees:
                remarques.append(f"stacks ajoutées depuis la dernière installation : {', '.join(ajoutees)}")
        elif not stacks and not autres:
            # Projet sans code : la stack sera choisie par architect, toutes restent disponibles
            # jusqu'à la relance qui suit la création du squelette.
            stacks = list(STACKS)
            nouveau = True
            remarques.append("projet sans code détecté : toutes les stacks sont installées ; relance la commande "
                             "après la création du squelette pour ne garder que les stacks retenues")
    else:
        stacks = [] if args.stack == "auto" else [s.strip() for s in args.stack.split(",")]
    for langage in filter(None, (l.strip().lower() for l in (args.langage or "").split(","))):
        stacks += LANGAGES[langage]
    return sorted(set(stacks), key=list(STACKS).index), remarques, nouveau


def desinstaller(base: Path, ancien: dict) -> int:
    if not ancien:
        print(f"Rien à désinstaller : pas de {MANIFESTE} dans {base}")
        return 1
    journal: list[str] = []
    for rel in ancien.get("fichiers", []):
        supprimer(base / rel, journal)
    retirer_reglages_claude(base, ancien.get("refus_ajoutes", []), ancien.get("autorisations_ajoutees", []), journal)
    retirer_bloc_agents_md(base, journal)
    retirer_dossiers_vides(base)
    (base / MANIFESTE).unlink()
    print(*journal, sep="\n")
    print("\nBibliothèque désinstallée. Les documents de suivi (docs/) sont conservés.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("projet", type=Path, nargs="?", default=Path.cwd(),
                        help="dossier du projet (défaut : dossier courant)")
    parser.add_argument("--stack",
                        help="auto (défaut) : détectées, toutes dans un projet sans code ; à la relance, celles de "
                             "l'installation plus celles apparues depuis. Sinon toutes, aucune, ou liste : " + ", ".join(STACKS))
    parser.add_argument("--langage", help="ajoute les stacks d'un langage : " + ", ".join(
        f"{l} ({', '.join(s)})" for l, s in LANGAGES.items()))
    parser.add_argument("--outil", choices=["auto", "claude", "codex", "les-deux"],
                        help="auto (défaut) : les outils trouvés dans le PATH, Claude Code sinon ; "
                             "à la relance, ceux de l'installation")
    parser.add_argument("--global", dest="global_", action="store_true",
                        help="installe dans ~/.claude et ~/.codex pour tous les projets")
    parser.add_argument("--force", action="store_true",
                        help="remplace aussi les fichiers qui n'ont pas été installés par ce script")
    parser.add_argument("--desinstaller", action="store_true", help="retire ce que ce script a installé")
    args = parser.parse_args()

    base = Path.home() if args.global_ else args.projet.resolve()
    if not base.is_dir():
        print(f"Dossier introuvable : {base}")
        return 1
    ancien = lire_json(base / MANIFESTE)
    if args.desinstaller:
        return desinstaller(base, ancien)
    # Relancer la commande sans option met à jour l'installation existante : mêmes stacks, plus
    # celles apparues depuis ; après un projet sans code, seulement celles du squelette créé.
    # En global, la relance garde les stacks choisies à l'identique.
    relance = bool(ancien) and args.stack is None and not args.langage
    if relance and args.global_:
        args.stack = ",".join(ancien["stacks"]) or "aucune"
    args.stack = args.stack or "auto"
    args.outil = args.outil or ancien.get("outil", "auto")

    mots_cles = ("auto", "toutes", "aucune")
    inconnues = [] if args.stack in mots_cles else [s.strip() for s in args.stack.split(",") if s.strip() not in STACKS]
    langues = [l.strip() for l in (args.langage or "").lower().split(",") if l.strip() and l.strip() not in LANGAGES]
    if inconnues or langues:
        print(f"Stack inconnue : {', '.join(inconnues)}. Stacks couvertes : {', '.join(STACKS)}." if inconnues else
              f"Langage non spécialisé : {', '.join(langues)}. Langages couverts : {', '.join(LANGAGES)}. "
              "Pour un autre langage, lance --stack aucune : les agents génériques s'appliquent.")
        return 1

    stacks, remarques, nouveau = choisir_stacks(args, base, ancien if relance else {})
    outil = outils_detectes() if args.outil == "auto" else args.outil
    rediges = skills_rediges()
    agents = agents_choisis(stacks)
    skills, absents = fermeture_skills(agents, rediges)
    inst = Installation(base, args.force, ancien)
    if outil in ("claude", "les-deux"):
        installer_claude(inst, agents, skills, rediges, args.global_, stacks)
    if outil in ("codex", "les-deux"):
        installer_codex(inst, agents, skills, rediges, args.global_)
    inst.retirer_obsoletes()
    ancien_outil = ancien.get("outil", "")
    if ancien_outil in ("claude", "les-deux") and outil == "codex":
        retirer_reglages_claude(base, inst.refus_ajoutes, inst.autorisations_ajoutees, inst.journal)
        inst.refus_ajoutes = []
        inst.autorisations_ajoutees = []
    if ancien_outil in ("codex", "les-deux") and outil == "claude":
        retirer_bloc_agents_md(base, inst.journal)
    retirer_dossiers_vides(base)
    inst.ecrire(base / MANIFESTE, json.dumps({
        "outil": outil, "stacks": stacks, "global": args.global_, "nouveau": nouveau,
        "fichiers": sorted(inst.fichiers), "refus_ajoutes": sorted(set(inst.refus_ajoutes)),
        "autorisations_ajoutees": sorted(set(inst.autorisations_ajoutees)),
    }, ensure_ascii=False, indent=2) + "\n")

    if not args.global_ and base != Path.home() and (Path.home() / MANIFESTE).exists():
        remarques.append("installation globale présente : les agents de ce projet prennent le dessus "
                         "sur ceux du même nom installés pour tous les projets")
    if not args.global_:
        a_relire = ["CLAUDE.md"] + (["AGENTS.md"] if outil == "claude" else [])
        for fichier in a_relire:
            if (base / fichier).exists():
                inst.journal.append(f"à relire : {fichier} existe déjà ; ses consignes s'appliquent aussi aux agents "
                                    "(principes communs, règle 1)")
    print(*inst.journal, sep="\n")
    print()
    print(*remarques, sep="\n")
    cible = "pour tous les projets (~/.claude, ~/.codex, ~/.agents)" if args.global_ else f"dans {base}"
    print(f"{len(agents)} agents et {len(skills)} skills installés {cible}, outil : {outil}, "
          f"stacks : {', '.join(stacks) or 'aucune'}.")
    if absents:
        print(f"Skills cités mais pas encore rédigés ({len(absents)}), signalés par les agents s'ils en ont besoin :")
        print("  " + ", ".join(sorted(absents)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
