---
name: env-secrets
description: Gérer la configuration par environnement et les secrets sans jamais lire, écrire ni afficher un secret réel - variables recensées depuis le code, .env.example complet et sans valeur, validation au démarrage, secrets dans le coffre de la plateforme, rien de secret dans un bundle client ou une image, recherche de secrets dans le code et l'historique sans les révéler. À utiliser pour créer ou modifier une variable d'environnement, initialiser un projet, configurer une CI ou un conteneur, et auditer les secrets.
---

# Variables d'environnement et secrets

Créer, lire, afficher ou faire tourner un secret réel est réservé à l'humain, et un secret n'est jamais écrit dans le code ni la documentation (règle 5 des principes communs). Le hook `actions-reservees.py` bloque la lecture et l'écriture de `.env`, `.env.local`, `.env.production`, des clés privées, de `auth.json`, `.npmrc` et des fichiers de credentials ; il laisse passer `.env.example`, `.env.dist`, `.env.sample`, `.env.template`, `.env.testing`, `.env.test` et `.env.ci`. Ce skill donne la méthode qui respecte ces deux garde-fous.

## Quand l'utiliser
- `scaffolder` : `.gitignore`, `.env.example`, chargement de la configuration par environnement.
- `devops-engineer` : variables de CI, de conteneur et de déploiement, intégration au gestionnaire de secrets.
- `security-auditor` et skill `owasp-checklist` : recherche de secrets dans le code et l'historique.
- Tout agent qui ajoute, renomme ou supprime une variable d'environnement.

## Ce que l'agent rate sans ce skill
- Il essaie de lire `.env` pour connaître une valeur, puis contourne le blocage (`php -r`, `printenv`, `env | grep`, script). Contourner le hook est une faute, pas une astuce.
- Il ajoute une variable dans le code sans l'ajouter à `.env.example`, ou l'inverse en laisse une morte.
- Il met une valeur plausible dans `.env.example` (clé de test d'un fournisseur, mot de passe `secret123`) qui finit en production.
- Il appelle `env()` hors de `config/` en Laravel : après `php artisan config:cache`, la valeur vaut `null`.
- Il met une clé dans une variable `NEXT_PUBLIC_*`, `EXPO_PUBLIC_*` ou dans `environment.ts` d'Angular : elle est copiée dans le bundle livré à tous.
- Il passe un secret en `ARG` ou `ENV` de Dockerfile : il reste lisible dans l'historique de l'image.
- Il affiche le secret trouvé dans son rapport ou une sortie de commande « pour preuve ».
- Il croit qu'effacer le fichier dans un nouveau commit suffit : le secret reste dans l'historique et doit être considéré comme compromis.

## Entrées
- Le code qui lit la configuration, `.env.example` (ou équivalent permis), `.gitignore`, la configuration versionnée (`config/`, `config/packages/`, `application*.yml`, `next.config.*`, `app.config.*`), les workflows de CI, les Dockerfile.

## Procédure
1. **Recenser les variables depuis le code**, jamais depuis `.env` :
   - Laravel : `rg -o "env\('[A-Z0-9_]+'" config/` ; Symfony : `rg -o "%env\([^)]*\)%" config/` ;
   - Spring Boot : `rg -o '\$\{[A-Z0-9_.]+' src/main/resources/` ;
   - Next.js, Node, Expo : `rg -o "process\.env\.[A-Z0-9_]+" --glob '!node_modules'`.
   Compare avec les clés de `.env.example` : chaque variable lue y figure, chaque clé du fichier est lue quelque part.
2. **Tenir `.env.example`** (gabarit dans « Livrable ») : toutes les clés, valeur vide pour un secret, valeur locale sans risque pour le reste (`localhost`, `APP_ENV=local`), un commentaire par groupe : rôle, format, obligatoire ou non, où l'obtenir. Les valeurs de test vont dans `.env.testing`, `.env.test` ou `phpunit.xml`, et sont manifestement factices.
3. **Vérifier `.gitignore`** : `.env`, `.env.local`, `.env.*.local`, `.env.production`, clés privées, `auth.json`, clés de déchiffrement du coffre Symfony (`config/secrets/*/*.decrypt.private.php`) ; contrôle avec `git check-ignore -v .env`.
4. **Lire la configuration au bon endroit** : `env()` seulement dans `config/*.php` (Laravel) ; `%env(...)%` avec processeurs typés (`int:`, `bool:`) en Symfony ; `@ConfigurationProperties` avec `@Validated` en Spring Boot ; un module unique qui valide `process.env` côté serveur en Next.js.
5. **Échouer au démarrage** si une variable obligatoire manque ou a un format faux, avec un message qui donne le nom de la variable, jamais sa valeur.
6. **Séparer public et secret** : tout ce qui part au navigateur ou dans l'application mobile est public. Un secret reste côté serveur, derrière une route ou une fonction serveur.
7. **Secrets hors dépôt** : coffre de la plateforme (secrets GitHub Actions lus par `${{ secrets.NOM }}`, variables d'environnement EAS, coffre de l'hébergeur), coffre Symfony (`secrets:set`) ou `.env` chiffré Laravel (`env:encrypt`) si le projet les utilise déjà. L'agent écrit le code qui lit le nom ; créer la valeur (`gh secret set`, `secrets:set`) est une action réservée : il prépare la liste des noms et l'endroit où les créer.
8. **Conteneurs et CI** : secrets de build par `RUN --mount=type=secret` (BuildKit), secrets d'exécution injectés par l'orchestrateur ; aucune commande qui affiche l'environnement (`env`, `printenv`, `set -x` autour d'un secret) dans un workflow.
9. **Rechercher les secrets sans les afficher** :
   - `gitleaks git --redact` (versions récentes) ou `gitleaks detect --redact` s'il est installé, sur l'arbre et l'historique ;
   - sinon des motifs connus en listant seulement les emplacements : `git grep -l -E '<motif>' $(git rev-list --all)` ou `rg -l -E '<motif>'` (motifs : `AKIA[0-9A-Z]{16}`, `-----BEGIN [A-Z ]*PRIVATE KEY-----`, `sk_live_`, `ghp_[A-Za-z0-9]{36}`, `xox[bp]-`).
   Le rapport donne le type de secret, le fichier, la ligne ou le commit, jamais la valeur.
10. **Secret réel trouvé** : arrêt de toute recopie, puis décision humaine : rotation d'abord, nettoyage de l'historique (`git filter-repo`) ensuite, car un secret poussé est compromis.

## Livrable
```dotenv
# Application
APP_ENV=local
APP_URL=http://localhost:8000

# Base de données (obligatoire) — valeurs locales de docker-compose
DB_HOST=127.0.0.1
DB_PASSWORD=

# Fournisseur de paiement (obligatoire en production) — clé secrète, côté serveur uniquement
# À créer dans le tableau de bord du fournisseur ; jamais de préfixe NEXT_PUBLIC_ ou EXPO_PUBLIC_
PAYMENT_SECRET_KEY=
```
Et dans le compte rendu : variables ajoutées, retirées ou renommées ; secrets à créer par l'humain (nom, environnement, coffre) dans « Décision humaine requise ».

## Vérifications
- Le recensement de l'étape 1 et les clés de `.env.example` concordent ; commandes citées.
- `git check-ignore -v .env` confirme l'exclusion ; `git ls-files | rg -i '\.env$|\.pem$|\.key$'` ne liste aucun fichier de secrets.
- Démarrage sans une variable obligatoire : échec avec le nom de la variable (test ou commande citée).
- Aucune valeur de secret dans le diff, le rapport ni les sorties citées.

## Limites
- L'agent ne connaît jamais les valeurs réelles : il ne vérifie pas qu'un secret de production est correct, il vérifie que le code le lit et échoue proprement s'il manque.
- `php artisan config:show <fichier>` affiche les valeurs chargées : à réserver aux fichiers sans secret (`app`, `cache`, `logging`), jamais `database`, `services` ou `mail`.

## En cas de blocage
- Une valeur réelle est indispensable pour avancer (appel à un service tiers) : bouchon ou valeur factice en test, et demande humaine préparée pour créer le secret.
- Symfony versionne `.env` avec des valeurs par défaut, mais le hook en bloque la lecture : recense depuis `config/` (étape 1) et documente les clés dans `.env.dist` ou le README si le projet n'a pas de fichier d'exemple.
