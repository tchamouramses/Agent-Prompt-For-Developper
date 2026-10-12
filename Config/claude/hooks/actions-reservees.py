#!/usr/bin/env python3
"""Hook PreToolUse de Claude Code : bloque techniquement les actions réservées à l'humain.

Règle 5 des principes communs. Les prompts demandent déjà aux agents de ne pas faire
ces actions ; ce hook les empêche même si un agent dérive ou suit une injection.

Bloque :
  - push vers la branche principale, push forcé, fusion ou publication via `gh` ;
  - commandes de déploiement, de publication et d'infrastructure ;
  - commandes de base destructrices hors environnement de test ;
  - lecture ou modification des fichiers de secrets (`.env`, clés privées) ;
  - pour les agents de contrôle, toute commande qui modifie le dépôt.

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
ENVIRONNEMENT_TEST = re.compile(r"--env[= ](testing|test)\b|\bAPP_ENV=(testing|test)\b|\bAPP_ENV=test\b")
MIGRATION_PRODUCTION = re.compile(r"\bartisan\s+migrate\b[^|;&]*--force\b")

ECRITURE_SHELL = [
    r"(^|[^0-9&=\-])>{1,2}(?!\s*(/dev/null|/tmp/|&|>))",
    r"\btee\b",
    r"\bsed\b[^|;&]*\s-i",
    r"\b(rm|mv|cp|mkdir|touch|chmod|chown|ln|truncate|patch)\s",
    r"\bgit\s+(add|commit|push|reset|checkout|switch|restore|stash|apply|am|cherry-pick|rebase|merge|clean|rm|mv|tag)\b",
    r"--fix\b|--write\b|\bpint\b(?![^|;&]*--test)|\bphp-cs-fixer\s+fix\b(?![^|;&]*--dry-run)|\brector\b(?![^|;&]*--dry-run)",
    r"\b(composer|npm|pnpm|yarn)\s+(require|remove|add|update|upgrade|uninstall)\b",
    r"\bartisan\s+(make:|migrate\b|db:seed)",
]


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


def verifier_bash(commande: str, agent: str) -> None:
    for segment in segments(commande):
        verifier_push(segment)
        for motif, libelle in DEPLOIEMENTS:
            if re.search(motif, segment):
                bloquer(libelle)
        if BASE_DESTRUCTRICE.search(segment) and not ENVIRONNEMENT_TEST.search(segment):
            bloquer("commande de base destructrice hors environnement de test (ajoute --env=testing sur une base de test)")
        if MIGRATION_PRODUCTION.search(segment):
            bloquer("migration forcée, réservée à la production")
        if LECTURE_SECRETS.search(segment) and any(est_secret(j) for j in jetons(segment)):
            bloquer("lecture d'un fichier de secrets")
        if agent in AGENTS_DE_CONTROLE:
            for motif in ECRITURE_SHELL:
                if re.search(motif, segment):
                    bloquer(f"l'agent de contrôle « {agent} » ne modifie pas le dépôt")


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
