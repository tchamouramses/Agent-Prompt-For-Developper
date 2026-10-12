---
name: readme-template
description: Écrire ou remettre à jour le README d'un projet - prérequis aux versions exactes, installation depuis un clone vierge, configuration sans secret, commandes réellement présentes dans le projet, structure, liens vers docs/ - et prouver chaque commande en l'exécutant. À utiliser pour créer le README d'un nouveau projet, le mettre à jour après un changement d'installation, de commande ou de configuration, ou le vérifier avant une version.
---

# README

La règle « tester chaque commande documentée » est dans l'agent `doc-writer` ; la règle « aucun secret dans la documentation » est la règle 5 des principes communs. Ce skill donne le gabarit et la façon de prouver qu'il marche.

## Quand l'utiliser
- `scaffolder` : premier README d'un projet. `doc-writer` : mise à jour après une fonctionnalité ou avant une version.
- Tout agent dont la tâche change une commande, un prérequis, une variable d'environnement ou une étape d'installation.

## Ce que l'agent rate sans ce skill
- Il laisse le README par défaut du framework (« About Laravel », texte de `create-next-app`) à côté du vrai contenu.
- Il écrit des commandes plausibles mais absentes : `npm test` alors que le script s'appelle `test:unit`, `composer dev` dans un projet sans ce script.
- Il oublie une étape qui « marche chez lui » parce que son environnement est déjà prêt : `php artisan key:generate`, `cp .env.example .env`, création de la base, `npm run build` pour les assets.
- Il recopie la version de sa mémoire au lieu de celle du projet (`.nvmrc`, `composer.json` `require.php`, toolchain Java).
- Il met une valeur réelle dans l'exemple de configuration, ou un badge de CI pour un workflow qui n'existe pas.
- Il duplique `docs/PROJECT.md` ou l'architecture au lieu d'y renvoyer.

## Entrées
- Manifestes et scripts : `composer.json` (`scripts`), `package.json` (`scripts`, `engines`), `pom.xml` ou `build.gradle`, `Makefile`, `.nvmrc`, `.tool-versions`, `docker-compose.yml`.
- `.env.example`, `.github/workflows/`, le README existant, `docs/PROJECT.md`, `docs/runbook.md`.

## Procédure
1. **Inventorier ce qui existe** : liste les scripts déclarés (`jq .scripts package.json`, `composer run-script --list`, `./gradlew tasks`, plugins déclarés dans `pom.xml`, cibles du `Makefile`). Seules ces commandes, et celles du framework, entrent dans le README.
2. **Relever les prérequis réels** : version du langage et du gestionnaire depuis les fichiers du projet (skill `version-compatibility`), services nécessaires (base, cache, file) depuis `docker-compose.yml` et `.env.example`.
3. **Écrire selon le gabarit** ci-dessous ; une section sans contenu réel est supprimée, pas laissée vide.
4. **Commandes par stack**, à adapter aux scripts du projet :
   - Laravel : `composer install`, `cp .env.example .env`, `php artisan key:generate`, `php artisan migrate`, `npm ci && npm run build`, `php artisan serve` (ou `composer run dev` si le script existe), `php artisan test`.
   - Symfony : `composer install`, `bin/console doctrine:migrations:migrate`, `symfony server:start` si la CLI Symfony est un prérequis, sinon `php -S localhost:8000 -t public`.
   - Spring Boot : `./mvnw spring-boot:run` ou `./gradlew bootRun`, `./mvnw verify` ou `./gradlew build`.
   - Angular : `npm ci`, `npx ng serve`, `npx ng test`, `npx ng build`. Next.js : `npm ci`, `npm run dev`, `npm run build`. Expo : `npm ci`, `npx expo start`.
5. **Configuration** : un tableau des variables de `.env.example` (nom, rôle, obligatoire ou non, valeur d'exemple factice). Les valeurs réelles viennent du gestionnaire de secrets ; dis où, jamais quoi.
6. **Prouver depuis un clone vierge** : `git worktree add /tmp/readme-check HEAD` (ou `git clone` local), puis exécute chaque commande du README dans l'ordre, telle qu'écrite. Corrige le README, pas ton environnement, à chaque écart. Retire le worktree ensuite (`git worktree remove /tmp/readme-check`).
7. **Nettoyer** : supprime le texte par défaut du framework, les sections devenues fausses, les badges sans cible.

## Livrable
```markdown
# <Nom du projet>
<Une phrase : ce que fait le projet et pour qui.>

## Prérequis
- PHP 8.3 (composer.json), Composer 2, Node 22 (.nvmrc), PostgreSQL 16 (docker-compose.yml)

## Installation
<commandes numérotées, copiables telles quelles>

## Configuration
| Variable | Rôle | Obligatoire | Exemple |
|----------|------|-------------|---------|

## Commandes
| Action | Commande |
|--------|----------|
| Lancer | … |
| Tester | … |
| Linter | … |
| Construire | … |

## Structure
<5 à 10 dossiers clés, une ligne chacun>

## Documentation
[État du projet](docs/PROJECT.md) · [Architecture](docs/architecture.md) · [API](docs/api.md) · [Exploitation](docs/runbook.md) · [Changelog](docs/CHANGELOG.md)
```

## Vérifications
- Chaque commande du README a été exécutée depuis un clone vierge dans cette session ; commandes et résultats cités dans le compte rendu.
- Chaque variable de `.env.example` figure dans le tableau, et inversement ; aucune valeur réelle.
- Chaque lien vers `docs/` et chaque badge pointe vers un fichier ou un workflow existant.

## Limites
- Le déploiement et le dépannage vont dans `docs/runbook.md` (`devops-engineer`) ; le README y renvoie.
- Une commande qui exige un service payant ou un compte tiers ne peut pas être prouvée : marque-la **non vérifiée**.

## En cas de blocage
- Une commande échoue depuis le clone vierge à cause du code (dépendance manquante, migration cassée) : documente l'état réel, signale le défaut à l'agent concerné et ajoute la tâche au plan ; n'écris pas une étape de contournement non tracée.
- Service impossible à lancer dans la session (base, conteneur) : prouve tout le reste et marque les étapes concernées **non vérifiées**.
