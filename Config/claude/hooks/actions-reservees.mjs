#!/usr/bin/env node
/**
 * Hook PreToolUse de Claude Code : bloque techniquement les actions réservées à l'humain.
 *
 * Règle 5 des principes communs. Les prompts demandent déjà aux agents de ne pas faire
 * ces actions ; ce hook les empêche même si un agent dérive ou suit une injection.
 *
 * Bloque :
 *   - push vers la branche principale, push forcé, fusion ou publication via `gh` ;
 *   - commandes de déploiement, de publication et d'infrastructure ;
 *   - commandes de base destructrices hors environnement de test ;
 *   - lecture ou modification des fichiers de secrets (`.env`, clés privées) ;
 *   - pour les agents de contrôle, toute écriture hors de /tmp (redirection, rm, cp, sed -i, git,
 *     correcteurs automatiques, ajout de dépendance, génération de code).
 *
 * C'est un garde-fou contre la dérive, pas une barrière contre un agent hostile : un script
 * (php, node) peut toujours écrire un fichier.
 *
 * Entrée : JSON du hook sur stdin. Sortie : code 2 et motif sur stderr pour bloquer.
 * Node.js 18 ou plus, sans dépendance.
 * Essai : echo '{"tool_name":"Bash","tool_input":{"command":"git push origin main"}}' | node actions-reservees.mjs
 */
import { readFileSync } from "node:fs";

const BRANCHES_PROTEGEES = new Set(["main", "master", "production", "prod", "release"]);
const AGENTS_DE_CONTROLE = new Set(["code-reviewer", "security-auditor", "quality-gatekeeper"]);

const FICHIERS_PERMIS = /\.env\.(example|dist|sample|template|testing|test|ci)$/;
const FICHIERS_SECRETS = new RegExp(
  String.raw`(^|/)(\.env(\.[\w.-]+)?|id_(rsa|ed25519|ecdsa)|[\w.-]+\.(pem|key|p12|pfx|jks|keystore)` +
    String.raw`|auth\.json|credentials(\.json)?|service-account[\w.-]*\.json|\.npmrc|\.pypirc)$`,
);
const LECTURE_SECRETS =
  /\b(cat|less|more|head|tail|grep|rg|ag|awk|sed|bat|nl|xxd|od|base64|strings|source|diff|cut|sort|uniq|jq|yq)\b/;

const DEPLOIEMENTS = [
  [/\bgh\s+pr\s+merge\b/, "fusion d'une PR"],
  [/\bgh\s+release\s+create\b/, "publication d'une version"],
  [/\bgh\s+workflow\s+run\b/, "lancement d'un workflow distant"],
  [/\b(npm|pnpm|yarn)\s+publish\b/, "publication d'un paquet"],
  [/\bcomposer\s+publish\b|\bmvn\s+deploy\b|\bgradlew?\s+publish\b/, "publication d'un paquet"],
  [/\bdocker\s+push\b/, "publication d'une image"],
  [/\bvercel\b.*(--prod\b|\bdeploy\b)|\bnetlify\s+deploy\b.*--prod/, "déploiement"],
  [/\b(fly|flyctl)\s+deploy\b|\bfirebase\s+deploy\b|\bheroku\s+(releases|container:release|deploy)/, "déploiement"],
  [/\b(serverless|sls|cdk|sam)\s+deploy\b|\bvapor\s+deploy\b|\bdep\s+deploy\b|\benvoy\s+run\b/, "déploiement"],
  [/\beas\s+(submit|update)\b|\beas\s+build\b.*--auto-submit/, "publication mobile"],
  [/\bkubectl\s+(apply|create|delete|patch|replace|rollout|scale|set|edit)\b/, "action sur un cluster"],
  [/\bhelm\s+(install|upgrade|uninstall|rollback|delete)\b/, "action sur un cluster"],
  [/\b(terraform|tofu)\s+(apply|destroy|import)\b|\bpulumi\s+(up|destroy)\b/, "action sur une infrastructure"],
];

const BASE_DESTRUCTRICE = new RegExp(
  String.raw`\bartisan\s+(migrate:fresh|migrate:reset|migrate:refresh|db:wipe)\b` +
    String.raw`|\bdoctrine:(database:drop|schema:drop)\b` +
    String.raw`|\bprisma\s+migrate\s+reset\b|\bflyway\s+clean\b` +
    String.raw`|\bdrop\s+(database|schema)\b`,
  "i",
);
const ENVIRONNEMENT_TEST = /--env[= ](testing|test)\b|\bAPP_ENV=(testing|test)\b|\bDB_DATABASE=(:memory:|\/tmp\/)/;
const MIGRATION_PRODUCTION = /\bartisan\s+migrate\b[^|;&]*--force\b/;

const TEMPORAIRES = ["/tmp/", "/dev/null", "/dev/stdout", "/dev/stderr", "$TMPDIR", "${TMPDIR"];
const VERBES_ECRITURE = new Set(["rm", "rmdir", "mv", "cp", "mkdir", "touch", "chmod", "chown", "ln", "truncate", "patch", "tee"]);
const GIT_ECRITURE = new Set(["add", "commit", "push", "reset", "checkout", "switch", "restore", "stash", "apply", "am",
  "cherry-pick", "rebase", "merge", "clean", "rm", "mv", "tag", "branch"]);
const GESTIONNAIRES = new Set(["composer", "npm", "pnpm", "yarn"]);
const GESTION_ECRITURE = new Set(["require", "remove", "add", "update", "upgrade", "uninstall"]);
const OPERATEURS = new Set(["|", "||", "&&", ";", "&", "(", ")", "\n", ";;"]);
const REDIRECTIONS = new Set([">", ">>", ">|", "&>", "&>>"]);
const PONCTUATION = "();<>|&\n";
const HEREDOC = /<<-?\s*(['"]?)(\w+)\1([^\n]*)\n[\s\S]*?\n\s*\2\s*(?=\n|$)/g;

class Bloque extends Error {}

function bloquer(motif) {
  throw new Bloque(
    `Bloqué par la règle 5 des principes communs : ${motif}. ` +
      "Prépare l'action et ajoute-la à la section « Décision humaine requise » de ton compte rendu.",
  );
}

/**
 * Découpe une commande comme un shell POSIX (guillemets, échappements).
 * Avec `ponctuation`, les suites d'opérateurs forment des jetons à part et `#` ouvre un commentaire.
 * Lève une erreur sur un guillemet non fermé.
 */
function decouper(texte, { ponctuation = false } = {}) {
  const blancs = ponctuation ? " \t\r" : " \t\r\n";
  const jetons = [];
  let jeton = "";
  let enCours = false; // un jeton (éventuellement vide, comme "") est commencé
  let etat = " "; // " " entre jetons, "a" dans un mot, "c" dans une ponctuation, "'" ou '"' dans des guillemets
  const fin = () => {
    if (enCours) jetons.push(jeton);
    jeton = "";
    enCours = false;
  };
  for (let i = 0; i < texte.length; i++) {
    const c = texte[i];
    if (etat === "'") {
      if (c === "'") etat = "a";
      else jeton += c;
      continue;
    }
    if (etat === '"') {
      if (c === '"') etat = "a";
      else if (c === "\\" && i + 1 < texte.length) {
        const suivant = texte[++i];
        jeton += suivant === "\\" || suivant === '"' ? suivant : "\\" + suivant;
      } else jeton += c;
      continue;
    }
    if (etat === "c") {
      if (PONCTUATION.includes(c)) {
        jeton += c;
        continue;
      }
      fin();
      etat = " ";
    }
    if (blancs.includes(c)) {
      fin();
      etat = " ";
    } else if (ponctuation && c === "#") {
      fin();
      etat = " ";
      const ligne = texte.indexOf("\n", i);
      i = ligne === -1 ? texte.length : ligne;
    } else if (ponctuation && PONCTUATION.includes(c)) {
      fin();
      jeton = c;
      enCours = true;
      etat = "c";
    } else if (c === "\\") {
      enCours = true;
      etat = "a";
      if (i + 1 < texte.length) jeton += texte[++i];
    } else if (c === "'" || c === '"') {
      enCours = true;
      etat = c;
    } else {
      jeton += c;
      enCours = true;
      etat = "a";
    }
  }
  if (etat === "'" || etat === '"') throw new Error("guillemet non fermé");
  fin();
  return jetons;
}

function estSecret(chemin) {
  chemin = chemin.replace(/^['"]+|['"]+$/g, "");
  return FICHIERS_SECRETS.test(chemin) && !FICHIERS_PERMIS.test(chemin);
}

function segments(commande) {
  return commande.split(/&&|\|\||;|\n/).map((s) => s.trim()).filter(Boolean);
}

function jetons(segment) {
  try {
    return decouper(segment);
  } catch {
    return segment.split(/\s+/).filter(Boolean);
  }
}

function verifierPush(segment) {
  const mots = jetons(segment);
  if (!mots.includes("git") || !mots.includes("push")) return;
  const apres = mots.slice(mots.indexOf("push") + 1);
  if (apres.some((m) => ["-f", "--force", "--mirror"].includes(m) || m.startsWith("+"))) bloquer("push forcé");
  for (const mot of apres) {
    const cible = mot.split(":").at(-1).replace(/^refs\/heads\//, "");
    if (BRANCHES_PROTEGEES.has(cible)) bloquer(`push vers la branche protégée « ${cible} »`);
  }
  if (apres.includes("--all") || apres.includes("--tags")) bloquer("push de toutes les branches ou de tous les tags");
}

const horsTemporaire = (chemin) => !TEMPORAIRES.some((t) => chemin.startsWith(t));

/** Retire le corps des heredocs écrits dans un fichier ; garde ceux donnés à un shell. */
function sansHeredoc(commande) {
  return commande.replace(HEREDOC, (tout, _q, _fin, reste, position) => {
    const debut = commande.slice(0, position).split("\n").at(-1);
    const shell = /\b(ba|z|da)?sh\s*$/.test(debut.trim()) || /\b(ba|z|da)?sh\b/.test(reste);
    return shell ? tout : reste;
  });
}

function commandesSimples(commande) {
  const liste = decouper(sansHeredoc(commande), { ponctuation: true });
  const commandes = [];
  const cibles = [];
  let courante = [];
  for (let i = 0; i < liste.length; i++) {
    const jeton = liste[i];
    if (REDIRECTIONS.has(jeton)) {
      if (i + 1 < liste.length) cibles.push(liste[i + 1]);
      i++;
      continue;
    }
    if (OPERATEURS.has(jeton) || (jeton && [...jeton].every((c) => PONCTUATION.includes(c)))) {
      if (courante.length) commandes.push(courante);
      courante = [];
    } else {
      courante.push(jeton);
    }
  }
  if (courante.length) commandes.push(courante);
  return [commandes, cibles];
}

function ecritureHorsTemporaire(commande) {
  let commandes, cibles;
  try {
    [commandes, cibles] = commandesSimples(commande);
  } catch {
    return "commande illisible";
  }
  for (const cible of cibles) {
    if (horsTemporaire(cible) && !/^\d+$/.test(cible)) return `redirection vers ${cible}`;
  }
  for (let mots of commandes) {
    while (mots.length && (/^\w+=/.test(mots[0]) || ["sudo", "command", "env", "time"].includes(mots[0]))) {
      mots = mots.slice(1);
    }
    if (!mots.length) continue;
    const nom = mots[0].split("/").at(-1);
    const args = mots.slice(1).filter((m) => !m.startsWith("-"));
    const options = mots.slice(1).filter((m) => m.startsWith("-"));
    const texte = mots.join(" ");
    if (VERBES_ECRITURE.has(nom)) {
      const vises = ["cp", "mv", "ln"].includes(nom) ? args.slice(-1) : args;
      if (vises.some(horsTemporaire)) return `${nom} ${vises.join(" ")}`;
    } else if (nom === "sed" && options.some((o) => o.startsWith("-i")) && args.length && horsTemporaire(args.at(-1))) {
      return `sed -i ${args.at(-1)}`;
    } else if (nom === "git" && args.length && GIT_ECRITURE.has(args[0]) && !(args[0] === "branch" && args.length === 1)) {
      return `git ${args[0]}`;
    } else if (GESTIONNAIRES.has(nom) && args.length && GESTION_ECRITURE.has(args[0])) {
      return `${nom} ${args[0]}`;
    } else if (nom === "pint" && !options.includes("--test")) {
      return "pint sans --test";
    } else if ((nom === "php-cs-fixer" || nom === "rector") && !options.includes("--dry-run")) {
      return `${nom} sans --dry-run`;
    } else if (options.includes("--fix") || options.includes("--write")) {
      return `${nom} ${options.includes("--fix") ? "--fix" : "--write"}`;
    } else if (nom === "php" && args.includes("artisan")) {
      const sous = args[args.indexOf("artisan") + 1] ?? "";
      if (sous.startsWith("make:")) return `artisan ${sous}`;
      if ((sous.startsWith("migrate") || sous.startsWith("db:seed")) && !ENVIRONNEMENT_TEST.test(`${texte} ${commande}`)) {
        return `artisan ${sous} hors base de test`;
      }
    }
  }
  return "";
}

function verifierBash(commande, agent) {
  for (const segment of segments(commande)) {
    verifierPush(segment);
    for (const [motif, libelle] of DEPLOIEMENTS) {
      if (motif.test(segment)) bloquer(libelle);
    }
    if (BASE_DESTRUCTRICE.test(segment) && !ENVIRONNEMENT_TEST.test(commande)) {
      bloquer("commande de base destructrice hors environnement de test (ajoute --env=testing sur une base de test)");
    }
    if (MIGRATION_PRODUCTION.test(segment) && !ENVIRONNEMENT_TEST.test(commande)) {
      bloquer("migration forcée, réservée à la production");
    }
    if (LECTURE_SECRETS.test(segment) && jetons(segment).some(estSecret)) {
      bloquer("lecture d'un fichier de secrets (pour une valeur de configuration, lis .env.example, " +
        "`php artisan about`, ou `php artisan config:show app` sur un fichier de configuration sans secret)");
    }
  }
  if (AGENTS_DE_CONTROLE.has(agent)) {
    const ecriture = ecritureHorsTemporaire(commande);
    if (ecriture) {
      bloquer(`l'agent de contrôle « ${agent} » ne modifie pas le dépôt (${ecriture}) ; écris tes fichiers d'essai dans /tmp`);
    }
  }
}

function main() {
  let donnees;
  try {
    donnees = JSON.parse(readFileSync(0, "utf8"));
  } catch {
    return 0;
  }
  const outil = donnees?.tool_name ?? "";
  const entree = donnees?.tool_input ?? {};
  const agent = donnees?.agent_type ?? "";
  try {
    if (outil === "Bash") {
      verifierBash(String(entree.command ?? ""), agent);
    } else if (["Read", "Edit", "Write", "MultiEdit", "NotebookEdit"].includes(outil)) {
      const chemin = String(entree.file_path ?? entree.notebook_path ?? "");
      if (estSecret(chemin)) {
        bloquer("accès à un fichier de secrets ; ajoute la clé sans valeur dans le fichier d'exemple (.env.example)");
      }
    }
  } catch (erreur) {
    if (!(erreur instanceof Bloque)) throw erreur;
    process.stderr.write(erreur.message + "\n");
    return 2;
  }
  return 0;
}

process.exitCode = main();
