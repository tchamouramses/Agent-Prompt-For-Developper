#!/usr/bin/env node
/**
 * Cas d'essai de scripts/install.mjs sur des projets jetables.
 *
 * Usage : node scripts/test-install.mjs
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const INSTALL = fileURLToPath(new URL("install.mjs", import.meta.url));
const echecs = [];

function lancer(args, { home, cwd }) {
  const resultat = spawnSync(process.execPath, [INSTALL, ...args], {
    cwd, env: { ...process.env, HOME: home, USERPROFILE: home }, encoding: "utf8",
  });
  return resultat.stdout + resultat.stderr;
}

function verifier(condition, cas) {
  if (!condition) echecs.push(cas);
}

function ecrire(chemin, contenu) {
  fs.mkdirSync(path.dirname(chemin), { recursive: true });
  fs.writeFileSync(chemin, contenu, "utf8");
}

const lire = (chemin) => fs.readFileSync(chemin, "utf8");
const lireJson = (chemin) => JSON.parse(lire(chemin));
const existe = (...parties) => fs.existsSync(path.join(...parties));
const lireManifeste = (projet) => lireJson(path.join(projet, ".bibliotheque-agents.json"));

function fichiers(dossier) {
  return fs.readdirSync(dossier, { recursive: true, withFileTypes: true })
    .filter((e) => e.isFile())
    .map((e) => path.relative(dossier, path.join(e.parentPath ?? e.path, e.name)).split(path.sep).join("/"))
    .sort();
}

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "test-install-"));
try {
  const home = path.join(tmp, "home");
  fs.mkdirSync(home);

  // Détection : Laravel avec Vite à la racine, Next.js dans un sous-dossier, Go non couvert.
  const lara = path.join(tmp, "lara");
  ecrire(path.join(lara, "composer.json"), '{"require": {"laravel/framework": "^11"}}');
  ecrire(path.join(lara, "package.json"), '{"devDependencies": {"vite": "^5"}}');
  ecrire(path.join(lara, ".claude", "agents", "planner.md"), "agent du projet\n");
  ecrire(path.join(lara, ".claude", "settings.json"),
    '{"permissions": {"allow": ["Bash(make:*)"], "deny": ["Bash(rm -rf:*)"]}}');
  ecrire(path.join(lara, "AGENTS.md"), "# Règles du projet\n");
  let sortie = lancer(["--outil", "les-deux"], { home, cwd: lara });
  verifier(sortie.includes("stacks détectées : laravel"), "détection de Laravel");
  verifier(!sortie.includes("non couvert"), "le package.json de Vite n'est pas un projet à part");
  verifier(existe(lara, ".claude", "agents", "laravel-implementer.md"), "agent Laravel installé");
  verifier(lire(path.join(lara, ".claude", "agents", "planner.md")) === "agent du projet\n",
    "fichier du projet conservé sans --force");
  verifier(existe(lara, ".codex", "agents", "laravel-implementer.toml"), "agent Codex installé");
  verifier(lire(path.join(lara, "AGENTS.md")).includes("Règles du projet"), "AGENTS.md du projet conservé");
  const reglages = lireJson(path.join(lara, ".claude", "settings.json"));
  const permis = new Set(reglages.permissions.allow);
  verifier(["Bash(make:*)", "Bash(git status:*)", "Bash(php:*)"].every((r) => permis.has(r)),
    "autorisations générales, de la stack et du projet");
  verifier(!permis.has("Bash(./mvnw:*)"), "pas d'autorisation d'une stack absente");
  verifier(existe(lara, ".claude", "hooks", "actions-reservees.mjs"), "hook installé");
  verifier(JSON.stringify(reglages.hooks).includes('node \\"$CLAUDE_PROJECT_DIR\\"/.claude/hooks/actions-reservees.mjs'),
    "hook lancé par node");

  // Relance sans option : même installation, mise à jour sur place.
  sortie = lancer([], { home, cwd: lara });
  verifier(sortie.includes("outil : les-deux, stacks : laravel"), "relance réutilise le manifeste");

  // Projet existant : une application ajoutée au dépôt est prise en compte à la relance.
  ecrire(path.join(lara, "front", "package.json"), '{"dependencies": {"next": "15"}}');
  sortie = lancer([], { home, cwd: lara });
  verifier(sortie.includes("stacks : laravel, nextjs"), "relance : stack ajoutée au dépôt");
  verifier(sortie.includes("stacks ajoutées depuis la dernière installation : nextjs"), "relance : ajout signalé");
  fs.rmSync(path.join(lara, "front"), { recursive: true });

  // Désinstallation : il ne reste que les fichiers du projet.
  lancer(["--desinstaller"], { home, cwd: lara });
  const restants = fichiers(lara);
  verifier(JSON.stringify(restants) === JSON.stringify([".claude/agents/planner.md", ".claude/settings.json", "AGENTS.md",
    "composer.json", "package.json"]), `désinstallation propre (${restants})`);
  const rendus = lireJson(path.join(lara, ".claude", "settings.json"));
  verifier(JSON.stringify(rendus.permissions) === JSON.stringify({ allow: ["Bash(make:*)"], deny: ["Bash(rm -rf:*)"] })
    && !("hooks" in rendus), "réglages du projet rendus");
  verifier(lire(path.join(lara, "AGENTS.md")).trim() === "# Règles du projet", "bloc AGENTS.md retiré");

  // Mise à jour d'une installation faite par l'ancienne version en Python : hook remplacé, pas doublé.
  const ancienne = path.join(tmp, "ancienne");
  ecrire(path.join(ancienne, "package.json"), '{"dependencies": {"next": "15"}}');
  ecrire(path.join(ancienne, ".claude", "hooks", "actions-reservees.py"), "# ancien hook\n");
  ecrire(path.join(ancienne, ".claude", "settings.json"), JSON.stringify({
    hooks: { PreToolUse: [{ matcher: "Bash", hooks: [{ type: "command",
      command: 'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/actions-reservees.py' }] }] },
  }));
  ecrire(path.join(ancienne, ".bibliotheque-agents.json"), JSON.stringify({
    outil: "claude", stacks: ["nextjs"], global: false, fichiers: [".claude/hooks/actions-reservees.py"],
  }));
  lancer([], { home, cwd: ancienne });
  const migres = JSON.stringify(lireJson(path.join(ancienne, ".claude", "settings.json")).hooks);
  verifier(!existe(ancienne, ".claude", "hooks", "actions-reservees.py"), "migration : ancien hook retiré");
  verifier(!migres.includes("actions-reservees.py") && migres.split("actions-reservees.mjs").length === 2,
    "migration : un seul hook, en Node.js");

  const mono = path.join(tmp, "mono");
  ecrire(path.join(mono, "apps", "web", "package.json"), '{"dependencies": {"next": "15"}}');
  ecrire(path.join(mono, "services", "outil", "go.mod"), "module outil\n");
  sortie = lancer(["--outil", "claude"], { home, cwd: mono });
  verifier(sortie.includes("stacks détectées : nextjs"), "détection dans un sous-dossier");
  verifier(sortie.includes("non couvert : Go"), "langage non couvert signalé");

  // Nouveau projet : sans code, toutes les stacks ; après le squelette, seulement la sienne.
  const neuf = path.join(tmp, "neuf");
  ecrire(path.join(neuf, "README.md"), "# Projet\n");
  sortie = lancer(["--outil", "claude"], { home, cwd: neuf });
  verifier(sortie.includes("projet sans code détecté") && sortie.includes("25 agents"), "nouveau projet : toutes les stacks");
  verifier(lireManifeste(neuf).nouveau === true, "nouveau projet : marqué dans le manifeste");
  ecrire(path.join(neuf, "composer.json"), '{"require": {"symfony/framework-bundle": "^7"}}');
  sortie = lancer([], { home, cwd: neuf });
  verifier(sortie.includes("stacks : symfony"), "nouveau projet : relance après le squelette");
  verifier(!existe(neuf, ".claude", "agents", "laravel-implementer.md"), "nouveau projet : agents des autres stacks retirés");
  verifier(lireManifeste(neuf).nouveau === false, "nouveau projet : devenu projet existant");

  // Langage : toutes les stacks TypeScript ; langage, stack ou option inconnus refusés.
  const vide = path.join(tmp, "vide");
  fs.mkdirSync(vide);
  sortie = lancer(["--langage", "typescript", "--outil", "claude"], { home, cwd: vide });
  verifier(sortie.includes("stacks : angular, nextjs, expo"), "--langage typescript");
  verifier(lancer(["--langage", "python"], { home, cwd: vide }).includes("Langage non spécialisé"), "langage refusé");
  verifier(lancer(["--stack", "django"], { home, cwd: vide }).includes("Stack inconnue"), "stack refusée");
  verifier(lancer(["--inconnue"], { home, cwd: vide }).includes("option inconnue"), "option refusée");

  // Global : ~/.claude et ~/.codex, sans toucher au config.toml de l'utilisateur.
  ecrire(path.join(home, ".codex", "config.toml"), 'model = "perso"\n');
  sortie = lancer(["--global", "--outil", "les-deux"], { home, cwd: vide });
  verifier(sortie.includes("25 agents"), "global : toutes les stacks");
  verifier(existe(home, ".claude", "agents", "expo-mobile-implementer.md"), "global : agents Claude");
  verifier(existe(home, ".agents", "skills", "laravel", "SKILL.md"), "global : skills Codex");
  verifier(lire(path.join(home, ".codex", "AGENTS.md")).includes("~/.codex/agents/"), "global : chemins Codex");
  verifier(lire(path.join(home, ".claude", "settings.json")).includes("$HOME"), "global : chemin du hook");
  verifier(lire(path.join(home, ".codex", "config.toml")) === 'model = "perso"\n', "global : config.toml intact");
  sortie = lancer([], { home, cwd: neuf });
  verifier(sortie.includes("installation globale présente"), "projet : installation globale signalée");
  lancer(["--global", "--stack", "laravel"], { home, cwd: vide });
  verifier(lancer(["--global"], { home, cwd: vide }).includes("stacks : laravel"), "global : relance à l'identique");
  lancer(["--global", "--desinstaller"], { home, cwd: vide });
  verifier(JSON.stringify(fichiers(home)) === JSON.stringify([".codex/config.toml"]), "global : désinstallation propre");
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}

for (const cas of echecs) console.log(`ÉCHEC : ${cas}`);
console.log(`${echecs.length ? "Échec" : "Tous les cas passent"} (${echecs.length} échec(s)).`);
process.exitCode = echecs.length ? 1 : 0;
