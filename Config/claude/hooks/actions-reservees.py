#!/usr/bin/env python3
"""Hook PreToolUse de Claude Code : bloque techniquement les actions réservées à l'humain.

Règle 5 des principes communs. Les prompts demandent déjà aux agents de ne pas faire
ces actions ; ce hook les empêche même si un agent dérive ou suit une injection.

Bloque :
  - push vers la branche principale, push forcé, fusion ou publication via `gh` ;
  - commandes de déploiement, de publication et d'infrastructure ;
  - commandes de base destructrices hors environnement de test ;
  - lecture ou modification des fichiers de secrets (`.env`, clés privées) ;
  - pour les agents de contrôle, toute écriture hors de /tmp (redirection, rm, cp, sed -i, git,
    correcteurs automatiques, ajout de dépendance, génération de code).

C'est un garde-fou contre la dérive, pas une barrière contre un agent hostile : un script
(php, python) peut toujours écrire un fichier.

Entrée : JSON du hook sur stdin. Sortie : code 2 et motif sur stderr pour bloquer.
Essai : echo '{"tool_name":"Bash","tool_input":{"command":"git push origin main"}}' | python3 actions-reservees.py
"""
import json
import re
import shlex
import sys

BRANCHES_PROTEGEES = {"main", "master", "production", "prod", "release"}
AGENTS_DE_CONTROLE = {"code-reviewer", "security-auditor", "quality-gatekeeper"}

FICHIERS_PERMIS = re.compile(r"\.env\.(example|dist|sample|template|testing|test|ci)$")
FICHIERS_SECRETS = re.compile(
    r"(^|/)(\.env(\.[\w.-]+)?|id_(rsa|ed25519|ecdsa)|[\w.-]+\.(pem|key|p12|pfx|jks|keystore)"
    r"|auth\.json|credentials(\.json)?|service-account[\w.-]*\.json|\.npmrc|\.pypirc)$"
)
LECTURE_SECRETS = re.compile(
    r"\b(cat|less|more|head|tail|grep|rg|ag|awk|sed|bat|nl|xxd|od|base64|strings|source|diff|cut|sort|uniq|jq|yq)\b"
)

DEPLOIEMENTS = [
    (r"\bgh\s+pr\s+merge\b", "fusion d'une PR"),
    (r"\bgh\s+release\s+create\b", "publication d'une version"),
    (r"\bgh\s+workflow\s+run\b", "lancement d'un workflow distant"),
    (r"\b(npm|pnpm|yarn)\s+publish\b", "publication d'un paquet"),
    (r"\bcomposer\s+publish\b|\bmvn\s+deploy\b|\bgradlew?\s+publish\b", "publication d'un paquet"),
    (r"\bdocker\s+push\b", "publication d'une image"),
    (r"\bvercel\b.*(--prod\b|\bdeploy\b)|\bnetlify\s+deploy\b.*--prod", "déploiement"),
    (r"\b(fly|flyctl)\s+deploy\b|\bfirebase\s+deploy\b|\bheroku\s+(releases|container:release|deploy)", "déploiement"),
    (r"\b(serverless|sls|cdk|sam)\s+deploy\b|\bvapor\s+deploy\b|\bdep\s+deploy\b|\benvoy\s+run\b", "déploiement"),
    (r"\beas\s+(submit|update)\b|\beas\s+build\b.*--auto-submit", "publication mobile"),
    (r"\bkubectl\s+(apply|create|delete|patch|replace|rollout|scale|set|edit)\b", "action sur un cluster"),
    (r"\bhelm\s+(install|upgrade|uninstall|rollback|delete)\b", "action sur un cluster"),
    (r"\b(terraform|tofu)\s+(apply|destroy|import)\b|\bpulumi\s+(up|destroy)\b", "action sur une infrastructure"),
]

BASE_DESTRUCTRICE = re.compile(
    r"\bartisan\s+(migrate:fresh|migrate:reset|migrate:refresh|db:wipe)\b"
    r"|\bdoctrine:(database:drop|schema:drop)\b"
    r"|\bprisma\s+migrate\s+reset\b|\bflyway\s+clean\b"
    r"|\bdrop\s+(database|schema)\b",
    re.IGNORECASE,
)
ENVIRONNEMENT_TEST = re.compile(
    r"--env[= ](testing|test)\b|\bAPP_ENV=(testing|test)\b|\bDB_DATABASE=(:memory:|/tmp/)"
)
MIGRATION_PRODUCTION = re.compile(r"\bartisan\s+migrate\b[^|;&]*--force\b")

TEMPORAIRES = ("/tmp/", "/dev/null", "/dev/stdout", "/dev/stderr", "$TMPDIR", "${TMPDIR")
VERBES_ECRITURE = {"rm", "rmdir", "mv", "cp", "mkdir", "touch", "chmod", "chown", "ln", "truncate", "patch", "tee"}
GIT_ECRITURE = {"add", "commit", "push", "reset", "checkout", "switch", "restore", "stash", "apply", "am",
                "cherry-pick", "rebase", "merge", "clean", "rm", "mv", "tag", "branch"}
GESTIONNAIRES = {"composer", "npm", "pnpm", "yarn"}
GESTION_ECRITURE = {"require", "remove", "add", "update", "upgrade", "uninstall"}
OPERATEURS = {"|", "||", "&&", ";", "&", "(", ")", "\n", ";;"}
REDIRECTIONS = {">", ">>", ">|", "&>", "&>>"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1([^\n]*)\n.*?\n\s*\2\s*(?=\n|$)", re.DOTALL)
def bloquer(motif: str) -> None:
    print(
        f"Bloqué par la règle 5 des principes communs : {motif}. "
        "Prépare l'action et ajoute-la à la section « Décision humaine requise » de ton compte rendu.",
        file=sys.stderr,
    )
    sys.exit(2)


def est_secret(chemin: str) -> bool:
    chemin = chemin.strip("'\"")
    return bool(FICHIERS_SECRETS.search(chemin)) and not FICHIERS_PERMIS.search(chemin)


def segments(commande: str) -> list[str]:
    return [s.strip() for s in re.split(r"&&|\|\||;|\n", commande) if s.strip()]


def jetons(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def verifier_push(segment: str) -> None:
    mots = jetons(segment)
    if "git" not in mots or "push" not in mots:
        return
    apres = mots[mots.index("push") + 1:]
    if any(m in ("-f", "--force", "--mirror") or m.startswith("+") for m in apres):
        bloquer("push forcé")
    for mot in apres:
        cible = mot.split(":")[-1].removeprefix("refs/heads/")
        if cible in BRANCHES_PROTEGEES:
            bloquer(f"push vers la branche protégée « {cible} »")
    if "--all" in apres or "--tags" in apres:
        bloquer("push de toutes les branches ou de tous les tags")


def hors_temporaire(chemin: str) -> bool:
    return not chemin.startswith(TEMPORAIRES)


def sans_heredoc(commande: str) -> str:
    """Retire le corps des heredocs écrits dans un fichier ; garde ceux donnés à un shell."""
    def remplacer(m: re.Match) -> str:
        debut = commande[:m.start()].rsplit("\n", 1)[-1]
        shell = re.search(r"\b(ba|z|da)?sh\s*$", debut.strip()) or re.search(r"\b(ba|z|da)?sh\b", m.group(3))
        return m.group(0) if shell else m.group(3)
    return HEREDOC.sub(remplacer, commande)


def commandes_simples(commande: str) -> tuple[list[list[str]], list[str]]:
    lex = shlex.shlex(sans_heredoc(commande), posix=True, punctuation_chars="();<>|&\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    jetons_ = list(lex)
    commandes, cibles, courante = [], [], []
    i = 0
    while i < len(jetons_):
        jeton = jetons_[i]
        if jeton in REDIRECTIONS:
            if i + 1 < len(jetons_):
                cibles.append(jetons_[i + 1])
            i += 2
            continue
        if jeton in OPERATEURS or set(jeton) <= set("();<>|&\n"):
            if courante:
                commandes.append(courante)
            courante = []
        else:
            courante.append(jeton)
        i += 1
    if courante:
        commandes.append(courante)
    return commandes, cibles


def ecriture_hors_temporaire(commande: str) -> str:
    try:
        commandes, cibles = commandes_simples(commande)
    except ValueError:
        return "commande illisible"
    for cible in cibles:
        if hors_temporaire(cible) and not cible.isdigit():
            return f"redirection vers {cible}"
    for mots in commandes:
        while mots and (re.match(r"^\w+=", mots[0]) or mots[0] in ("sudo", "command", "env", "time")):
            mots = mots[1:]
        if not mots:
            continue
        nom = mots[0].rsplit("/", 1)[-1]
        args = [m for m in mots[1:] if not m.startswith("-")]
        options = [m for m in mots[1:] if m.startswith("-")]
        texte = " ".join(mots)
        if nom in VERBES_ECRITURE:
            vises = args[-1:] if nom in ("cp", "mv", "ln") else args
            if any(hors_temporaire(a) for a in vises):
                return f"{nom} {' '.join(vises)}"
        elif nom == "sed" and any(o.startswith("-i") for o in options) and args and hors_temporaire(args[-1]):
            return f"sed -i {args[-1]}"
        elif nom == "git" and args and args[0] in GIT_ECRITURE and not (args[0] == "branch" and len(args) == 1):
            return f"git {args[0]}"
        elif nom in GESTIONNAIRES and args and args[0] in GESTION_ECRITURE:
            return f"{nom} {args[0]}"
        elif nom == "pint" and "--test" not in options:
            return "pint sans --test"
        elif nom in ("php-cs-fixer", "rector") and "--dry-run" not in options:
            return f"{nom} sans --dry-run"
        elif "--fix" in options or "--write" in options:
            return f"{nom} {'--fix' if '--fix' in options else '--write'}"
        elif nom == "php" and "artisan" in args:
            sous = args[args.index("artisan") + 1] if args.index("artisan") + 1 < len(args) else ""
            if sous.startswith("make:"):
                return f"artisan {sous}"
            if sous.startswith(("migrate", "db:seed")) and not ENVIRONNEMENT_TEST.search(texte + " " + commande):
                return f"artisan {sous} hors base de test"
    return ""


def verifier_bash(commande: str, agent: str) -> None:
    for segment in segments(commande):
        verifier_push(segment)
        for motif, libelle in DEPLOIEMENTS:
            if re.search(motif, segment):
                bloquer(libelle)
        if BASE_DESTRUCTRICE.search(segment) and not ENVIRONNEMENT_TEST.search(commande):
            bloquer("commande de base destructrice hors environnement de test (ajoute --env=testing sur une base de test)")
        if MIGRATION_PRODUCTION.search(segment) and not ENVIRONNEMENT_TEST.search(commande):
            bloquer("migration forcée, réservée à la production")
        if LECTURE_SECRETS.search(segment) and any(est_secret(j) for j in jetons(segment)):
            bloquer("lecture d'un fichier de secrets (pour une valeur de configuration, lis .env.example, "
                    "`php artisan about`, ou `php artisan config:show app` sur un fichier de configuration sans secret)")
    if agent in AGENTS_DE_CONTROLE:
        ecriture = ecriture_hors_temporaire(commande)
        if ecriture:
            bloquer(f"l'agent de contrôle « {agent} » ne modifie pas le dépôt ({ecriture}) ; "
                    "écris tes fichiers d'essai dans /tmp")


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    outil = donnees.get("tool_name", "")
    entree = donnees.get("tool_input") or {}
    agent = donnees.get("agent_type") or ""
    if outil == "Bash":
        verifier_bash(entree.get("command", ""), agent)
    elif outil in ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit"):
        chemin = entree.get("file_path") or entree.get("notebook_path") or ""
        if est_secret(chemin):
            bloquer("accès à un fichier de secrets ; ajoute la clé sans valeur dans le fichier d'exemple (.env.example)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
