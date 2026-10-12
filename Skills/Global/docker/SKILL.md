---
name: docker
description: Conteneuriser une application proprement - Dockerfile multi-étapes, image de base minimale et versionnée, utilisateur non root, ordre des couches pour le cache, .dockerignore, aucun secret dans l'image, configuration lue au démarrage, healthcheck, docker compose pour le développement local ; docker push vers un registre reste une action réservée. À utiliser pour créer ou corriger un Dockerfile, un .dockerignore ou un compose.yaml, réduire une image ou réparer un build de conteneur.
---

# Docker

L'agent `devops-engineer` fixe les exigences (multi-étapes, image minimale, non root, `.dockerignore`, compose pour le développement). Ce skill donne la méthode et les pièges. Pousser une image vers un registre partagé, ou la lancer sur un environnement partagé, relève de la règle 5 des principes communs.

## Quand l'utiliser
- `devops-engineer` : tout Dockerfile, `.dockerignore`, `compose.yaml` ou `docker-compose.yml`.
- Tout agent qui ajoute un service de développement local (base, cache, file, serveur de mails de test).

## Ce que l'agent rate sans ce skill
- Il copie tout le dépôt avant d'installer les dépendances : chaque modification de code réinstalle tout.
- Il oublie le `.dockerignore` et embarque `.git`, `.env`, `node_modules`, `vendor` ou les sauvegardes locales dans l'image.
- Il passe un secret en `ARG` ou `ENV` : il reste lisible dans `docker history` et dans l'image.
- Il fige la configuration au build (`php artisan config:cache`, variables `NEXT_PUBLIC_*` de production) avec les valeurs de la machine de build.
- Il utilise `latest` comme image de base, garde les outils de build dans l'image finale, ou tourne en root.
- Il écrit `CMD` sous forme shell (`CMD npm start`) : le processus ne reçoit pas `SIGTERM` et l'arrêt prend le délai maximal.
- Son `depends_on` n'attend pas que la base soit prête.

## Entrées
- Commandes de build et de lancement du projet, version du langage, `docs/architecture.md`, services nécessaires (`.env.example`), Dockerfile et compose existants.

## Procédure
1. **Choisir l'image de base** officielle, à la version du projet, variante minimale (`-slim`, `-alpine` si les extensions natives le permettent) : `php:8.3-fpm`, `eclipse-temurin:21-jre`, `node:22-slim`. Pas de `latest` ; digest `@sha256:` si le projet épingle déjà.
2. **Étapes séparées** : `deps` (dépendances), `build` (compilation, assets), `runtime` (le strict nécessaire). Copie d'abord les fichiers de verrouillage, installe, puis copie le code.
3. **Par stack** :
   - Laravel ou Symfony : étape Composer `composer install --no-dev --prefer-dist --no-scripts --optimize-autoloader`, étape Node pour `npm ci && npm run build` si Vite ou Encore ; image finale PHP-FPM (avec serveur web séparé) ou FrankenPHP, extensions installées par `docker-php-ext-install` ; `config:cache`, `route:cache` (Laravel) et `cache:warmup` (Symfony) au démarrage du conteneur, pas au build.
   - Spring Boot : build `./mvnw -B package -DskipTests` dans une image JDK (les tests tournent dans la CI, pas ici), image finale JRE ; couches extraites avec `java -Djarmode=tools -jar app.jar extract --layers --launcher` (Spring Boot 3.3 et plus ; `-Djarmode=layertools` avant).
   - Next.js : `output: 'standalone'` dans `next.config`, copie de `.next/standalone`, `.next/static` et `public`, lancement `node server.js`. Les variables `NEXT_PUBLIC_*` sont figées au build : une image par environnement, ou configuration lue côté serveur.
   - Angular : `npx ng build` puis fichiers statiques servis par `nginxinc/nginx-unprivileged`, avec repli vers `index.html` pour le routage.
   - Expo et React Native : pas d'image applicative ; Docker sert au plus aux services de développement.
4. **Non root** : `USER` d'un utilisateur dédié (ou `node`, `www-data` selon l'image), fichiers copiés avec `--chown`, seuls les dossiers d'écriture (`storage/`, `var/`, cache) lui appartiennent.
5. **Secrets** : aucun dans l'image ; au build, `RUN --mount=type=secret,id=<nom>` ; à l'exécution, variables fournies par la plateforme (skill `env-secrets`). `.env` jamais copié.
6. **Exécution** : `CMD` ou `ENTRYPOINT` en forme tableau (`["node", "server.js"]`), `EXPOSE` du port réel, `HEALTHCHECK` sur un endpoint de santé (`/up` Laravel 11 et plus, `/actuator/health` Spring Boot) si la plateforme ne le fait pas.
7. **Compose de développement** : services avec versions de production, `healthcheck` sur la base et `depends_on: { db: { condition: service_healthy } }`, volumes nommés pour les données, code monté en volume pour le rechargement, identifiants factices, ports liés à `127.0.0.1`.
8. **Construire et tester localement** (permis, local) : build, lancement, santé, puis arrêt avec `docker compose down` (sans `-v` si les données de développement doivent rester).

## Livrable
```gitignore
# .dockerignore
.git
.env
.env.*
!.env.example
node_modules
vendor
coverage
storage/logs
*.log
```
Dans le compte rendu : taille de l'image, utilisateur d'exécution, commande de build et de lancement, et, si une publication est voulue, le bloc « Décision humaine requise » avec `docker push <registre>/<image>:<version>` prêt.

## Vérifications
- `docker build -t <image>:dev .` réussit ; `docker run --rm <image>:dev id -u` ne renvoie pas `0`.
- `docker compose up -d --wait` rend tous les services sains ; l'endpoint de santé répond.
- `docker history --no-trunc <image>:dev` et `docker run --rm <image>:dev ls -a` ne montrent ni secret, ni `.env`, ni `.git`.
- `hadolint` passe s'il est disponible (`docker run --rm -i hadolint/hadolint < Dockerfile`).

## Limites
- `docker push`, `docker login` avec de vrais identifiants, création d'un registre ou d'un compte : réservés (règle 5).
- L'orchestration de production (Kubernetes, plateforme managée) est une brique d'infrastructure : `architect` la décide, l'humain l'engage.

## En cas de blocage
- Docker absent de la session : écris les fichiers, marque build et lancement **non vérifiés**, et donne les commandes exactes de vérification.
- Extension native qui ne compile pas sur `alpine` : passe à la variante `-slim` (Debian) et consigne le choix.
