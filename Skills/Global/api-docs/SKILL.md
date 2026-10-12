---
name: api-docs
description: Produire la documentation d'une API à partir du code - spécification OpenAPI générée par l'outil de la stack (Scramble, Scribe, NelmioApiDocBundle, API Platform, springdoc) ou tenue à côté du code, validée par un linter, avec authentification, erreurs et exemples tirés de réponses réelles, et docs/api.md comme point d'entrée. À utiliser pour documenter un endpoint nouveau ou modifié, mettre à jour la référence d'API avant une version, ou vérifier que la documentation décrit encore le code.
---

# Documentation d'API

La documentation ne décrit que ce que le code fait (agent `doc-writer`). Le contrat, ses conventions (dates, montants, erreurs, pagination) et sa compatibilité relèvent du skill `api-contracts` : ce skill ne les redéfinit pas, il les rend lisibles et vérifiables.

## Quand l'utiliser
- `doc-writer` : référence d'API avant une version ou après une fonctionnalité livrée.
- Agents d'implémentation back : endpoint créé ou modifié dans un projet qui versionne sa spécification.
- `code-reviewer` : diff qui change une route, une requête ou une réponse sans toucher la documentation.

## Ce que l'agent rate sans ce skill
- Il écrit la spécification à la main à côté d'un générateur déjà installé : deux sources divergent dès le changement suivant.
- Il documente l'API de sa mémoire (champs attendus, codes « logiques ») au lieu de la réponse réelle : un champ renvoyé n'apparaît pas, un 422 est documenté en 400.
- Ses exemples sont inventés et ne passent pas la validation du schéma qu'ils illustrent.
- Il omet l'authentification, les erreurs (401, 403, 404, 422, 429) et la pagination, c'est-à-dire ce qu'un consommateur cherche en premier.
- Il laisse une valeur réelle dans un exemple : jeton, e-mail ou identifiant de production.
- Il ne régénère pas la spécification après le changement, et le fichier versionné décrit l'ancien comportement.

## Entrées
- Les routes (`php artisan route:list --json`, `bin/console debug:router`, contrôleurs Spring, `app/api/**/route.ts`), les classes de sérialisation et de validation, les tests de contrat (skill `api-contracts`).
- Le générateur présent dans les dépendances, la spécification versionnée (`openapi.yaml`, `docs/openapi.json`), `docs/api.md`.

## Procédure
1. **Trouver la source de vérité** (skill `api-contracts`, étape 1). Si un générateur est installé, il fait foi ; sinon le fichier OpenAPI versionné ; sinon, pour une API consommée par un front ou un mobile, ajoute le générateur standard de la stack selon la règle 4 des principes communs et consigne le choix.
2. **Générer depuis le code**, avec l'outil de la stack :
   - Laravel : `dedoc/scramble` (déduit les schémas des Form Requests et API Resources ; `php artisan scramble:export`) ou `knuckleswtf/scribe` (`php artisan scribe:generate`) ;
   - Symfony : API Platform (`bin/console api:openapi:export --yaml`) ou NelmioApiDocBundle (`bin/console nelmio:apidoc:dump --format=yaml`) ;
   - Spring Boot : `springdoc-openapi`, spécification servie sur `/v3/api-docs.yaml` par l'application lancée en profil de test, enregistrée dans le dépôt ;
   - Next.js (route handlers) : pas de générateur standard ; schémas `zod` existants convertis si l'outil est déjà présent, sinon `openapi.yaml` tenu à côté du code et contrôlé par les tests de contrat.
3. **Compléter ce que le générateur ne voit pas**, par les annotations ou attributs de l'outil, jamais en éditant le fichier généré : schéma de sécurité (Bearer, cookie de session, clé), réponses d'erreur par endpoint, description d'une règle métier non évidente, paramètres de pagination et de tri.
4. **Exemples réels** : prends le corps de requête et de réponse d'un test de contrat qui passe (données de factory, jamais de production), remplace toute valeur sensible par une valeur factice stable, et place-le comme `example` du schéma.
5. **Valider** : `npx @redocly/cli lint <spec>` (ou le linter déjà en place), puis la validation des réponses des tests contre la spécification si le projet l'a (skill `api-contracts`, étape 6).
6. **Tenir `docs/api.md`** comme point d'entrée court : URL de base par environnement (sans secret), authentification pas à pas, conventions communes en renvoyant à la spécification, lien vers la spécification et vers l'interface de consultation si le générateur en sert une.
7. **Côté consommateurs** (Angular, Next.js, Expo) : si le projet génère ses types depuis la spécification (`npx openapi-typescript <spec> -o <fichier>`), régénère-les dans le même changement.
8. **Changement cassant** : la documentation le marque (`deprecated: true`, date ou version de retrait) conformément à la transition décidée dans le skill `api-contracts` ; le skill `changelog-semver` en tire la ligne de changelog.

## Livrable
```markdown
# API
- Spécification : [openapi.yaml](../openapi.yaml), générée par <outil> (`<commande>`)
- Base : `https://<hôte>/api/v1` (production), `http://localhost:8000/api/v1` (développement)

## Authentification
<obtenir un jeton, l'envoyer, durée de vie, erreur renvoyée sans jeton>

## Conventions
Dates, montants, pagination, format d'erreur : voir `components/schemas` de la spécification.

## Endpoints
| Méthode | Chemin | Rôle | Auth | Erreurs |
|---------|--------|------|------|---------|
```

## Vérifications
- La spécification a été régénérée après le dernier changement de code ; `git diff` de la spécification cité et cohérent avec le diff du code.
- Le linter passe sans erreur ; chaque exemple est valide contre son schéma.
- Chaque route de `route:list` (ou équivalent) figure dans la spécification, et inversement, hors routes internes listées comme telles.

## Limites
- La forme des URL et des ressources relève du skill `api-design` ; ce skill documente l'existant.
- Publier la documentation sur un portail ou un service externe est un message externe (règle 5) : prépare-le, ne l'envoie pas.

## En cas de blocage
- Le générateur ne déduit pas une réponse (réponse construite à la main, tableau anonyme) : documente-la par attribut et ajoute au plan la tâche de passer par une classe de sérialisation.
- Code et spécification se contredisent : le code fait foi ; corrige la documentation et signale l'écart à `product-analyst` si la spec fonctionnelle dit autre chose.
