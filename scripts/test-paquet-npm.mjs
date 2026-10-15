#!/usr/bin/env node
/**
 * Vérifie le paquet npm : son contenu, puis une installation comme dépendance d'un projet
 * (`npx agents-dev`) et un lancement ponctuel (`npx --package <archive> agents-dev`).
 * Node.js 18 ou plus, npm, sans dépendance.
 */
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const NPM = process.platform === "win32" ? "npm.cmd" : "npm";
const NPX = process.platform === "win32" ? "npx.cmd" : "npx";
const temp = fs.mkdtempSync(path.join(os.tmpdir(), "paquet-npm-"));
let echecs = 0;

function verifier(condition, message) {
  if (!condition) echecs += 1;
  console.log(`${condition ? "ok " : "ÉCHEC"} ${message}`);
}
function lancer(commande, args, cwd) {
  return execFileSync(commande, args, { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], shell: process.platform === "win32" });
}
function projet(nom, dependances) {
  const dossier = path.join(temp, nom);
  fs.mkdirSync(dossier);
  fs.writeFileSync(path.join(dossier, "package.json"), JSON.stringify({ name: nom, private: true, dependencies: dependances }));
  return dossier;
}
const manifeste = (dossier) => JSON.parse(fs.readFileSync(path.join(dossier, ".bibliotheque-agents.json"), "utf8"));

try {
  const sortie = JSON.parse(lancer(NPM, ["pack", "--json", "--pack-destination", temp], ROOT));
  const fichiers = sortie[0].files.map((f) => f.path);
  const archive = path.join(temp, sortie[0].filename);
  verifier(fichiers.includes("scripts/install.mjs"), "le paquet contient l'installateur");
  verifier(fichiers.some((f) => f.startsWith("Skills/")) && fichiers.some((f) => f.startsWith("Agent/Global/")), "le paquet contient agents et skills");
  verifier(!fichiers.some((f) => f.startsWith("docs/") || f.startsWith(".github/")), "le paquet exclut docs/ et .github/");

  const dependance = projet("dependance", { next: "15.0.0" });
  lancer(NPM, ["install", "--save-dev", "--no-audit", "--no-fund", archive], dependance);
  const installe = lancer(NPX, ["agents-dev", "--outil", "claude"], dependance);
  verifier(installe.includes("stacks : nextjs"), "npx agents-dev depuis une dépendance détecte la stack");
  verifier(fs.existsSync(path.join(dependance, ".claude", "agents", "nextjs-implementer.md")), "agents copiés dans le projet");
  verifier(manifeste(dependance).relance === "npx agents-dev", "relance enregistrée : npx agents-dev");
  lancer(NPX, ["agents-dev", "--desinstaller"], dependance);
  verifier(!fs.existsSync(path.join(dependance, ".claude")), "désinstallation par npx");

  const ponctuel = projet("ponctuel", { "@angular/core": "19.0.0" });
  const sortiePonctuelle = lancer(NPX, ["--yes", "--package", archive, "agents-dev", "--outil", "claude"], ponctuel);
  verifier(sortiePonctuelle.includes("stacks : angular"), "npx --package <archive> installe sans dépendance");
  const relancePonctuelle = manifeste(ponctuel).relance;
  verifier(relancePonctuelle.startsWith("npx --yes ") && relancePonctuelle.endsWith(sortie[0].filename), `relance enregistrée : source rappelée par npx (${relancePonctuelle})`);

  const clone = projet("clone", {});
  lancer(process.execPath, [path.join(ROOT, "scripts", "install.mjs"), "--outil", "claude", "--stack", "aucune"], clone);
  verifier(manifeste(clone).relance === "agents-dev", "relance depuis un clone : agents-dev");
} finally {
  fs.rmSync(temp, { recursive: true, force: true });
}

console.log(`${echecs ? "Échecs" : "Tous les cas passent"} (${echecs} échec(s)).`);
process.exit(echecs ? 1 : 0);
