#!/usr/bin/env node
/**
 * Installe les agents, les skills et les garde-fous de cette bibliothèque dans un projet ou pour tous les projets.
 *
 * Installe les agents globaux, l'agent d'implémentation de chaque stack retenue, tous les skills
 * rédigés qu'ils citent (directement ou par un autre skill), et les réglages qui imposent les
 * actions réservées. Pour Claude Code, il autorise aussi sans confirmation les commandes de
 * développement générales puis celles des stacks retenues (Config/claude/autorisations-stacks.json),
 * pour que les agents avancent sans attendre l'humain ; les refus et le hook passent toujours avant.
 * Les stacks sont détectées dans le projet si aucune n'est donnée.
 *
 * Un manifeste (.bibliotheque-agents.json) liste ce qui a été installé : relancer la commande met
 * à jour ces fichiers et retire ceux devenus inutiles ; --desinstaller les retire tous. Un fichier
 * du projet qui n'a pas été installé par ce script n'est jamais écrasé sans --force.
 *
 * Node.js 18 ou plus, sans dépendance.
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const AIDE = `Usage :
  node scripts/install.mjs [dossier-du-projet] [--stack auto|laravel,nextjs|toutes|aucune]
                           [--langage php,java,typescript] [--outil auto|claude|codex|les-deux]
                           [--global] [--force] [--desinstaller]

  --stack        auto (défaut) : détectées, toutes dans un projet sans code ; à la relance, celles de
                 l'installation plus celles apparues depuis. Sinon toutes, aucune, ou liste :
                 laravel, symfony, spring-boot, angular, nextjs, expo
  --langage      ajoute les stacks d'un langage : php (laravel, symfony), java (spring-boot),
                 typescript (angular, nextjs, expo)
  --outil        auto (défaut) : les outils trouvés dans le PATH, Claude Code sinon ; à la relance,
                 ceux de l'installation
  --global       installe dans ~/.claude et ~/.codex pour tous les projets
  --force        remplace aussi les fichiers qui n'ont pas été installés par ce script
  --desinstaller retire ce que ce script a installé

Exemples :
  node scripts/install.mjs                            projet courant, stacks et outils détectés
  node scripts/install.mjs ~/mon-api --stack laravel  stack imposée
  node scripts/install.mjs --langage typescript       agents Angular, Next.js et Expo
  node scripts/install.mjs --global                   ~/.claude et ~/.codex, toutes les stacks
  node scripts/install.mjs --desinstaller             retire ce qui a été installé ici`;

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PAQUET_NPM = "@tchamouramses/agents-dev";

/** Commande qui relance cette installation, enregistrée dans le manifeste pour les agents. */
function commandeDeRelance(base) {
  const morceaux = ROOT.split(path.sep);
  if (!morceaux.includes("node_modules")) return "agents-dev";
  // Dépendance npm du projet : npx la trouve dans node_modules.
  if (fs.existsSync(path.join(base, "node_modules", ...PAQUET_NPM.split("/")))) return "npx agents-dev";
  // Cache de npx : son package.json garde la source demandée (registre, github:…, archive).
  const cache = morceaux.slice(0, morceaux.lastIndexOf("node_modules")).join(path.sep);
  const source = (lireJson(path.join(cache, "package.json")).dependencies || {})[PAQUET_NPM];
  const registre = !source || /^[\^~]?\d/.test(source);
  return `npx --yes ${registre ? PAQUET_NPM : source}`;
}
const MANIFESTE = ".bibliotheque-agents.json";
const HOOK = "actions-reservees.mjs";
const STACKS = {
  laravel: "PHP/laravel-implementer.md",
  symfony: "PHP/symfony-implementer.md",
  "spring-boot": "Java/spring-boot-implementer.md",
  angular: "TypeScript/angular-implementer.md",
  nextjs: "TypeScript/nextjs-implementer.md",
  expo: "TypeScript/expo-mobile-implementer.md",
};
const ORDRE_STACKS = Object.keys(STACKS);
const LANGAGES = { php: ["laravel", "symfony"], java: ["spring-boot"], typescript: ["angular", "nextjs", "expo"] };
const NON_COUVERTS = {
  "go.mod": "Go", "pyproject.toml": "Python", "requirements.txt": "Python", "Cargo.toml": "Rust",
  "pubspec.yaml": "Dart/Flutter", Gemfile: "Ruby", "mix.exs": "Elixir",
};
const IGNORES = new Set(["node_modules", "vendor", ".git", "dist", "build", "target", ".next", ".expo", "storage"]);
const MENTION = /skills? `([a-z0-9-]+)`/g;

const lire = (chemin) => fs.readFileSync(chemin, "utf8");
const json = (valeur) => JSON.stringify(valeur, null, 2) + "\n";
const trier = (liste) => [...liste].sort();
const dedans = (base, rel) => path.join(base, ...rel.split("/"));

// --- Choix des agents et skills -------------------------------------------------------------

function skillsRediges() {
  const rediges = new Map();
  for (const langage of fs.readdirSync(path.join(ROOT, "Skills"))) {
    const dossier = path.join(ROOT, "Skills", langage);
    if (!fs.statSync(dossier).isDirectory()) continue;
    for (const nom of fs.readdirSync(dossier)) {
      if (fs.existsSync(path.join(dossier, nom, "SKILL.md"))) rediges.set(nom, path.join(dossier, nom));
    }
  }
  return rediges;
}

function cites(texte) {
  const noms = new Set([...texte.matchAll(MENTION)].map((m) => m[1]));
  const entete = texte.startsWith("---\n") ? (texte.split("---\n")[1] ?? "") : "";
  for (const m of entete.matchAll(/^ {2}- ([a-z0-9-]+)$/gm)) noms.add(m[1]);
  return noms;
}

function agentsChoisis(stacks) {
  const global = path.join(ROOT, "Agent", "Global");
  const agents = trier(fs.readdirSync(global).filter((f) => f.endsWith(".md"))).map((f) => path.join(global, f));
  return [...agents, ...stacks.map((s) => path.join(ROOT, "Agent", ...STACKS[s].split("/")))];
}

function fermetureSkills(agents, rediges) {
  const aVoir = new Set();
  for (const agent of agents) for (const nom of cites(lire(agent))) aVoir.add(nom);
  const retenus = new Set();
  const absents = new Set();
  while (aVoir.size) {
    const nom = aVoir.values().next().value;
    aVoir.delete(nom);
    if (retenus.has(nom) || absents.has(nom)) continue;
    if (!rediges.has(nom)) {
      absents.add(nom);
      continue;
    }
    retenus.add(nom);
    for (const autre of cites(lire(path.join(rediges.get(nom), "SKILL.md")))) aVoir.add(autre);
  }
  return [retenus, absents];
}

// --- Détection ------------------------------------------------------------------------------

/** Parcourt la racine et les sous-dossiers jusqu'à `profondeur` (apps/web, packages/api…). */
function* fichiersMarqueurs(projet, profondeur = 2) {
  let dossiers = [projet];
  for (let niveau = 0; niveau <= profondeur; niveau++) {
    const suivants = [];
    for (const dossier of dossiers) {
      let enfants;
      try {
        enfants = fs.readdirSync(dossier, { withFileTypes: true });
      } catch {
        continue;
      }
      for (const enfant of enfants) {
        const chemin = path.join(dossier, enfant.name);
        if (enfant.isFile()) yield chemin;
        else if (enfant.isDirectory() && !IGNORES.has(enfant.name) && !enfant.name.startsWith(".")) suivants.push(chemin);
      }
    }
    dossiers = suivants;
  }
}

function lireJson(chemin) {
  try {
    const valeur = JSON.parse(lire(chemin));
    return valeur && typeof valeur === "object" && !Array.isArray(valeur) ? valeur : {};
  } catch {
    return {};
  }
}

/** Retourne les stacks couvertes trouvées et les langages vus sans stack couverte (langage -> fichier). */
function detecter(projet) {
  const stacks = new Set();
  const autres = new Map();
  const couverts = new Set();
  const autre = (langage, relatif, dossier) => {
    if (!autres.has(langage)) autres.set(langage, [relatif, dossier]);
  };
  for (const fichier of fichiersMarqueurs(projet)) {
    const relatif = path.relative(projet, fichier).split(path.sep).join("/");
    const nom = path.basename(fichier);
    const dossier = path.dirname(fichier);
    if (nom === "composer.json") {
      const donnees = lireJson(fichier);
      const paquets = { ...donnees.require, ...donnees["require-dev"] };
      if ("laravel/framework" in paquets) {
        stacks.add("laravel");
        couverts.add(dossier);
      } else if ("symfony/framework-bundle" in paquets) {
        stacks.add("symfony");
        couverts.add(dossier);
      } else autre("PHP sans Laravel ni Symfony", relatif, dossier);
    } else if (["pom.xml", "build.gradle", "build.gradle.kts"].includes(nom)) {
      if (lire(fichier).includes("spring-boot")) {
        stacks.add("spring-boot");
        couverts.add(dossier);
      } else autre("Java ou Kotlin sans Spring Boot", relatif, dossier);
    } else if (nom === "package.json") {
      const donnees = lireJson(fichier);
      const paquets = { ...donnees.dependencies, ...donnees.devDependencies };
      const stack = "expo" in paquets ? "expo" : "next" in paquets ? "nextjs" : "@angular/core" in paquets ? "angular" : "";
      if (stack) {
        stacks.add(stack);
        couverts.add(dossier);
      } else if (Object.keys(paquets).length) autre("JavaScript/TypeScript sans Angular, Next.js ni Expo", relatif, dossier);
    } else if (nom in NON_COUVERTS) {
      autre(NON_COUVERTS[nom], relatif, dossier);
    } else if (nom.endsWith(".csproj")) {
      autre(".NET", relatif, dossier);
    }
  }
  // Un package.json à côté d'un composer.json Laravel (Vite) n'est pas un projet JavaScript à part.
  const nonCouverts = new Map([...autres].filter(([, [, dossier]]) => !couverts.has(dossier)).map(([l, [rel]]) => [l, rel]));
  return [trier(stacks), nonCouverts];
}

function trouverCommande(nom) {
  const extensions = process.platform === "win32" ? (process.env.PATHEXT || ".EXE;.CMD;.BAT").split(";") : [""];
  for (const dossier of (process.env.PATH || "").split(path.delimiter)) {
    for (const extension of extensions) {
      try {
        const chemin = path.join(dossier, nom + extension);
        if (fs.statSync(chemin).isFile()) return chemin;
      } catch {
        // absent de ce dossier
      }
    }
  }
  return "";
}

function outilsDetectes() {
  const claude = trouverCommande("claude");
  const codex = trouverCommande("codex");
  if (claude && codex) return "les-deux";
  return codex && !claude ? "codex" : "claude";
}

// --- Écriture -------------------------------------------------------------------------------

/** Copie les fichiers et tient le manifeste de ce qui appartient à la bibliothèque. */
class Installation {
  constructor(base, force, ancien) {
    this.base = base;
    this.force = force;
    this.anciens = new Set(ancien.fichiers ?? []);
    this.fichiers = [];
    this.refusAjoutes = [...(ancien.refus_ajoutes ?? [])];
    this.autorisationsAjoutees = [...(ancien.autorisations_ajoutees ?? [])];
    this.journal = [];
  }

  rel(cible) {
    return path.relative(this.base, cible).split(path.sep).join("/");
  }

  copier(source, cible, toujours = false) {
    const rel = this.rel(cible);
    if (fs.existsSync(cible) && !(this.force || toujours || this.anciens.has(rel))) {
      this.journal.push(`conservé (existe déjà, pas installé par ce script) : ${cible}`);
      return;
    }
    fs.mkdirSync(path.dirname(cible), { recursive: true });
    if (fs.statSync(source).isDirectory()) {
      fs.rmSync(cible, { recursive: true, force: true });
      fs.cpSync(source, cible, { recursive: true });
    } else {
      fs.copyFileSync(source, cible);
    }
    this.fichiers.push(rel);
    this.journal.push(`${this.anciens.has(rel) ? "mis à jour" : "installé"} : ${cible}`);
  }

  ecrire(cible, contenu) {
    fs.mkdirSync(path.dirname(cible), { recursive: true });
    fs.writeFileSync(cible, contenu, "utf8");
  }

  retirerObsoletes() {
    const gardes = new Set(this.fichiers);
    for (const rel of trier(this.anciens)) if (!gardes.has(rel)) supprimer(dedans(this.base, rel), this.journal);
  }
}

function supprimer(chemin, journal) {
  if (!fs.existsSync(chemin)) return;
  fs.rmSync(chemin, { recursive: true, force: true });
  journal.push(`retiré : ${chemin}`);
}

function commandeHook(global) {
  const racine = global ? '"$HOME"' : '"$CLAUDE_PROJECT_DIR"';
  return `node ${racine}/.claude/hooks/${HOOK}`;
}

/** Repère l'entrée du hook, y compris l'ancienne version en Python. */
const estNotreHook = (entree) => JSON.stringify(entree).includes("actions-reservees.");

/** Commandes générales de settings.json, puis celles des stacks retenues (autorisations-stacks.json). */
function autorisations(modele, stacks) {
  const parStack = lireJson(path.join(ROOT, "Config", "claude", "autorisations-stacks.json"));
  const regles = [...modele.permissions.allow];
  for (const stack of stacks) for (const r of parStack[stack] ?? []) if (!regles.includes(r)) regles.push(r);
  return regles;
}

function fusionnerReglagesClaude(inst, global, stacks) {
  const modele = JSON.parse(lire(path.join(ROOT, "Config", "claude", "settings.json")));
  const cible = path.join(inst.base, ".claude", "settings.json");
  const actuel = fs.existsSync(cible) ? lireJson(cible) : {};
  const permissions = (actuel.permissions ??= {});
  const refus = (permissions.deny ??= []);
  for (const regle of modele.permissions.deny) {
    if (!refus.includes(regle)) {
      refus.push(regle);
      inst.refusAjoutes.push(regle);
    }
  }
  // Les autorisations suivent les stacks : celles d'une stack retirée disparaissent à la relance.
  const voulues = autorisations(modele, stacks);
  const permis = (permissions.allow ?? []).filter((r) => !inst.autorisationsAjoutees.includes(r) || voulues.includes(r));
  inst.autorisationsAjoutees = inst.autorisationsAjoutees.filter((r) => voulues.includes(r));
  for (const regle of voulues) {
    if (!permis.includes(regle)) {
      permis.push(regle);
      inst.autorisationsAjoutees.push(regle);
    }
  }
  permissions.allow = permis;
  const hooks = (actuel.hooks ??= {});
  const pre = (hooks.PreToolUse ?? []).filter((h) => !estNotreHook(h));
  for (const entree of structuredClone(modele.hooks.PreToolUse)) {
    for (const h of entree.hooks) h.command = commandeHook(global);
    pre.push(entree);
  }
  hooks.PreToolUse = pre;
  actuel.$schema ??= modele.$schema;
  inst.ecrire(cible, json(actuel));
  inst.journal.push(`fusionné : ${cible}`);
}

function retirerReglagesClaude(base, refusAjoutes, autorisationsAjoutees, journal) {
  const cible = path.join(base, ".claude", "settings.json");
  if (!fs.existsSync(cible)) return;
  const actuel = lireJson(cible);
  const permissions = actuel.permissions ?? {};
  if (permissions.deny) permissions.deny = permissions.deny.filter((r) => !refusAjoutes.includes(r));
  if (permissions.allow) permissions.allow = permissions.allow.filter((r) => !autorisationsAjoutees.includes(r));
  if (actuel.hooks?.PreToolUse) actuel.hooks.PreToolUse = actuel.hooks.PreToolUse.filter((h) => !estNotreHook(h));
  for (const [cle, enfant] of [["permissions", "allow"], ["permissions", "deny"], ["hooks", "PreToolUse"]]) {
    if (Array.isArray(actuel[cle]?.[enfant]) && actuel[cle][enfant].length === 0) delete actuel[cle][enfant];
    if (actuel[cle] && typeof actuel[cle] === "object" && Object.keys(actuel[cle]).length === 0) delete actuel[cle];
  }
  if (Object.keys(actuel).every((k) => k === "$schema")) {
    supprimer(cible, journal);
    return;
  }
  fs.writeFileSync(cible, json(actuel), "utf8");
  journal.push(`nettoyé : ${cible}`);
}

function retirerDossiersVides(base) {
  const vider = (dossier) => {
    for (const enfant of fs.readdirSync(dossier, { withFileTypes: true })) {
      if (enfant.isDirectory()) vider(path.join(dossier, enfant.name));
    }
    if (fs.readdirSync(dossier).length === 0) fs.rmdirSync(dossier);
  };
  for (const racine of [".claude", ".codex", ".agents"]) {
    const dossier = path.join(base, racine);
    if (fs.existsSync(dossier) && fs.statSync(dossier).isDirectory()) vider(dossier);
  }
}

const DEBUT_BLOC = "<!-- BIBLIOTHEQUE-AGENTS:DEBUT -->";
const FIN_BLOC = "<!-- BIBLIOTHEQUE-AGENTS:FIN -->";

function remplacerBloc(actuel, bloc) {
  if (actuel.includes(DEBUT_BLOC) && actuel.includes(FIN_BLOC)) {
    const [avant, ...reste] = actuel.split(DEBUT_BLOC);
    const apres = reste.join(DEBUT_BLOC).split(FIN_BLOC).slice(1).join(FIN_BLOC).replace(/^\n+/, "");
    if (bloc) return avant + bloc + apres;
    return avant.trim() ? avant.trimEnd() + "\n" + apres : apres;
  }
  if (!bloc) return actuel;
  return (actuel.trim() ? actuel.trimEnd() + "\n\n" : "") + bloc;
}

function retirerBlocAgentsMd(base, journal) {
  for (const agentsMd of [path.join(base, "AGENTS.md"), path.join(base, ".codex", "AGENTS.md")]) {
    if (fs.existsSync(agentsMd) && lire(agentsMd).includes(DEBUT_BLOC)) {
      const reste = remplacerBloc(lire(agentsMd), "");
      if (reste.trim()) fs.writeFileSync(agentsMd, reste, "utf8");
      else fs.unlinkSync(agentsMd);
      journal.push(`bloc retiré : ${agentsMd}`);
    }
  }
}

/** Ajoute les instructions Codex entre marqueurs, sans effacer celles déjà présentes. */
function fusionnerAgentsMd(inst, global) {
  let texte = lire(path.join(ROOT, "Codex", "AGENTS.md")).trim();
  if (global) texte = texte.replaceAll("`.codex/agents/", "`~/.codex/agents/");
  const cible = path.join(inst.base, global ? ".codex/AGENTS.md" : "AGENTS.md");
  const actuel = fs.existsSync(cible) ? lire(cible) : "";
  const nouveau = remplacerBloc(actuel, `${DEBUT_BLOC}\n${texte}\n${FIN_BLOC}\n`);
  inst.ecrire(cible, nouveau);
  const taille = Buffer.byteLength(nouveau, "utf8");
  inst.journal.push(`fusionné : ${cible} (${taille} octets)`);
  if (taille > 32 * 1024) {
    inst.journal.push("attention : AGENTS.md dépasse 32 Kio, limite par défaut de Codex (project_doc_max_bytes)");
  }
}

function installerClaude(inst, agents, skills, rediges, global, stacks) {
  for (const agent of agents) inst.copier(agent, path.join(inst.base, ".claude", "agents", path.basename(agent)));
  for (const nom of trier(skills)) inst.copier(rediges.get(nom), path.join(inst.base, ".claude", "skills", nom));
  inst.copier(path.join(ROOT, "Config", "claude", "hooks", HOOK), path.join(inst.base, ".claude", "hooks", HOOK), true);
  fusionnerReglagesClaude(inst, global, stacks);
}

function installerCodex(inst, agents, skills, rediges, global) {
  fusionnerAgentsMd(inst, global);
  for (const agent of agents) {
    const toml = path.join(ROOT, "Codex", "agents", `${path.basename(agent, ".md")}.toml`);
    inst.copier(toml, path.join(inst.base, ".codex", "agents", path.basename(toml)));
  }
  for (const nom of trier(skills)) inst.copier(rediges.get(nom), path.join(inst.base, ".agents", "skills", nom));
  if (!global) {
    // ~/.codex/config.toml appartient à l'utilisateur : on n'y touche pas.
    inst.copier(path.join(ROOT, "Config", "codex", "config.toml"), path.join(inst.base, ".codex", "config.toml"));
  }
  inst.copier(path.join(ROOT, "Config", "codex", "rules", "actions-reservees.rules"),
    path.join(inst.base, ".codex", "rules", "actions-reservees.rules"), true);
}

// --- Commande -------------------------------------------------------------------------------

/**
 * Retourne les stacks retenues, les remarques à afficher et si le projet est encore sans code.
 *
 * `precedent` est le manifeste d'une installation que l'on relance sans option ; ses stacks sont
 * gardées et complétées par celles détectées depuis (une application ajoutée au dépôt).
 */
function choisirStacks(args, projet, precedent) {
  const remarques = [];
  let nouveau = false;
  let stacks;
  if (args.stack === "aucune") {
    stacks = [];
  } else if (args.stack === "toutes" || (args.stack === "auto" && args.global && !args.langage)) {
    stacks = [...ORDRE_STACKS];
  } else if (args.stack === "auto" && !args.langage) {
    let autres;
    [stacks, autres] = detecter(projet);
    remarques.push(`stacks détectées : ${stacks.join(", ") || "aucune"}`);
    for (const [langage, fichier] of autres) remarques.push(`non couvert : ${langage} (${fichier}), agents génériques seulement`);
    if (Object.keys(precedent).length && !precedent.nouveau) {
      const anciennes = precedent.stacks ?? [];
      const ajoutees = stacks.filter((s) => !anciennes.includes(s));
      stacks = [...new Set([...stacks, ...anciennes])];
      if (ajoutees.length) remarques.push(`stacks ajoutées depuis la dernière installation : ${ajoutees.join(", ")}`);
    } else if (!stacks.length && !autres.size) {
      // Projet sans code : la stack sera choisie par architect, toutes restent disponibles
      // jusqu'à la relance qui suit la création du squelette.
      stacks = [...ORDRE_STACKS];
      nouveau = true;
      remarques.push("projet sans code détecté : toutes les stacks sont installées ; relance la commande " +
        "après la création du squelette pour ne garder que les stacks retenues");
    }
  } else {
    stacks = args.stack === "auto" ? [] : args.stack.split(",").map((s) => s.trim());
  }
  for (const langage of (args.langage ?? "").split(",").map((l) => l.trim().toLowerCase()).filter(Boolean)) {
    stacks.push(...LANGAGES[langage]);
  }
  const retenues = [...new Set(stacks)].sort((a, b) => ORDRE_STACKS.indexOf(a) - ORDRE_STACKS.indexOf(b));
  return [retenues, remarques, nouveau];
}

function desinstaller(base, ancien) {
  if (!Object.keys(ancien).length) {
    console.log(`Rien à désinstaller : pas de ${MANIFESTE} dans ${base}`);
    return 1;
  }
  const journal = [];
  for (const rel of ancien.fichiers ?? []) supprimer(dedans(base, rel), journal);
  retirerReglagesClaude(base, ancien.refus_ajoutes ?? [], ancien.autorisations_ajoutees ?? [], journal);
  retirerBlocAgentsMd(base, journal);
  retirerDossiersVides(base);
  fs.unlinkSync(path.join(base, MANIFESTE));
  console.log(journal.join("\n"));
  console.log("\nBibliothèque désinstallée. Les documents de suivi (docs/) sont conservés.");
  return 0;
}

function lireArguments(argv) {
  const args = { projet: process.cwd(), global: false, force: false, desinstaller: false };
  const avecValeur = { "--stack": "stack", "--langage": "langage", "--outil": "outil" };
  for (let i = 0; i < argv.length; i++) {
    let [option, valeur] = argv[i].startsWith("--") ? argv[i].split(/=(.*)/s) : [argv[i]];
    if (option === "-h" || option === "--help") {
      console.log(AIDE);
      process.exit(0);
    } else if (option in avecValeur) {
      valeur ??= argv[++i];
      if (valeur === undefined) throw new Error(`${option} attend une valeur`);
      args[avecValeur[option]] = valeur;
    } else if (option === "--global") args.global = true;
    else if (option === "--force") args.force = true;
    else if (option === "--desinstaller") args.desinstaller = true;
    else if (option.startsWith("-")) throw new Error(`option inconnue : ${option}`);
    else args.projet = argv[i];
  }
  if (args.outil && !["auto", "claude", "codex", "les-deux"].includes(args.outil)) {
    throw new Error(`--outil : choisis auto, claude, codex ou les-deux (pas ${args.outil})`);
  }
  return args;
}

function main() {
  let args;
  try {
    args = lireArguments(process.argv.slice(2));
  } catch (erreur) {
    console.log(`${erreur.message}\n\n${AIDE}`);
    return 2;
  }
  const base = args.global ? os.homedir() : path.resolve(args.projet);
  if (!fs.existsSync(base) || !fs.statSync(base).isDirectory()) {
    console.log(`Dossier introuvable : ${base}`);
    return 1;
  }
  const ancien = lireJson(path.join(base, MANIFESTE));
  if (args.desinstaller) return desinstaller(base, ancien);
  // Relancer la commande sans option met à jour l'installation existante : mêmes stacks, plus
  // celles apparues depuis ; après un projet sans code, seulement celles du squelette créé.
  // En global, la relance garde les stacks choisies à l'identique.
  const relance = Object.keys(ancien).length > 0 && args.stack === undefined && !args.langage;
  if (relance && args.global) args.stack = (ancien.stacks ?? []).join(",") || "aucune";
  args.stack ??= "auto";
  args.outil ??= ancien.outil ?? "auto";

  const motsCles = ["auto", "toutes", "aucune"];
  const inconnues = motsCles.includes(args.stack) ? [] : args.stack.split(",").map((s) => s.trim()).filter((s) => !(s in STACKS));
  const langues = (args.langage ?? "").toLowerCase().split(",").map((l) => l.trim()).filter((l) => l && !(l in LANGAGES));
  if (inconnues.length) {
    console.log(`Stack inconnue : ${inconnues.join(", ")}. Stacks couvertes : ${ORDRE_STACKS.join(", ")}.`);
    return 1;
  }
  if (langues.length) {
    console.log(`Langage non spécialisé : ${langues.join(", ")}. Langages couverts : ${Object.keys(LANGAGES).join(", ")}. ` +
      "Pour un autre langage, lance --stack aucune : les agents génériques s'appliquent.");
    return 1;
  }

  const [stacks, remarques, nouveau] = choisirStacks(args, base, relance ? ancien : {});
  const outil = args.outil === "auto" ? outilsDetectes() : args.outil;
  const rediges = skillsRediges();
  const agents = agentsChoisis(stacks);
  const [skills, absents] = fermetureSkills(agents, rediges);
  const inst = new Installation(base, args.force, ancien);
  if (outil === "claude" || outil === "les-deux") installerClaude(inst, agents, skills, rediges, args.global, stacks);
  if (outil === "codex" || outil === "les-deux") installerCodex(inst, agents, skills, rediges, args.global);
  inst.retirerObsoletes();
  const ancienOutil = ancien.outil ?? "";
  if ((ancienOutil === "claude" || ancienOutil === "les-deux") && outil === "codex") {
    retirerReglagesClaude(base, inst.refusAjoutes, inst.autorisationsAjoutees, inst.journal);
    inst.refusAjoutes = [];
    inst.autorisationsAjoutees = [];
  }
  if ((ancienOutil === "codex" || ancienOutil === "les-deux") && outil === "claude") retirerBlocAgentsMd(base, inst.journal);
  retirerDossiersVides(base);
  inst.ecrire(path.join(base, MANIFESTE), json({
    outil, stacks, global: args.global, nouveau, relance: commandeDeRelance(base),
    fichiers: trier(inst.fichiers), refus_ajoutes: trier(new Set(inst.refusAjoutes)),
    autorisations_ajoutees: trier(new Set(inst.autorisationsAjoutees)),
  }));

  if (!args.global && base !== os.homedir() && fs.existsSync(path.join(os.homedir(), MANIFESTE))) {
    remarques.push("installation globale présente : les agents de ce projet prennent le dessus " +
      "sur ceux du même nom installés pour tous les projets");
  }
  if (!args.global) {
    for (const fichier of ["CLAUDE.md", ...(outil === "claude" ? ["AGENTS.md"] : [])]) {
      if (fs.existsSync(path.join(base, fichier))) {
        inst.journal.push(`à relire : ${fichier} existe déjà ; ses consignes s'appliquent aussi aux agents ` +
          "(principes communs, règle 1)");
      }
    }
  }
  console.log(inst.journal.join("\n"));
  console.log();
  console.log(remarques.join("\n"));
  const cible = args.global ? "pour tous les projets (~/.claude, ~/.codex, ~/.agents)" : `dans ${base}`;
  console.log(`${agents.length} agents et ${skills.size} skills installés ${cible}, outil : ${outil}, ` +
    `stacks : ${stacks.join(", ") || "aucune"}.`);
  if (absents.size) {
    console.log(`Skills cités mais pas encore rédigés (${absents.size}), signalés par les agents s'ils en ont besoin :`);
    console.log("  " + trier(absents).join(", "));
  }
  return 0;
}

const [major] = process.versions.node.split(".").map(Number);
if (major < 18) {
  console.log(`Node.js 18 ou plus est requis (version trouvée : ${process.versions.node}).`);
  process.exitCode = 1;
} else {
  process.exitCode = main();
}
