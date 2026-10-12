---
name: error-handling
description: Traiter les erreurs explicitement et au bon endroit - classer l'erreur (validation, règle métier, absence, droits, panne transitoire, bug), exceptions métier typées, conservation de la cause, traduction en réponse HTTP en un seul point, messages sans fuite interne, délais et nouvelles tentatives limitées aux pannes transitoires, transactions annulées, erreurs asynchrones, écrans d'erreur front et mobile, tests des chemins d'échec. À utiliser pour tout code qui appelle un service externe, la base ou le système de fichiers, qui lève ou attrape une exception, ou qui affiche une erreur à l'utilisateur.
---

# Gestion des erreurs

Règle des principes des agents qui modifient du code (« Typage et erreurs ») : les erreurs sont traitées ou propagées explicitement, jamais avalées en silence. Ce skill dit où et comment. Le format des erreurs d'API est dans les skills `api-design` (catalogue RFC 9457) et `api-contracts` (statuts) ; ce qu'on journalise relève du skill `logging`.

## Quand l'utiliser
- `implementer` et agents d'implémentation des frameworks : tout code qui peut échouer ou qui affiche un échec.
- `code-reviewer` : `catch` vide, `catch (Exception)` générique, erreur transformée en `null`.

## Ce que l'agent rate sans ce skill
- Il entoure tout d'un `try/catch` qui journalise et continue : la commande est marquée payée alors que le paiement a échoué.
- Il relance une nouvelle exception sans la cause d'origine : la trace qui expliquait la panne disparaît.
- Il journalise et relance au même niveau : la même erreur apparaît cinq fois dans les journaux.
- Il renvoie le message de l'exception au client : requête SQL, chemin de fichier ou nom de classe exposés.
- Il réessaie une erreur qui ne guérira pas (422, 404, règle métier violée), ou réessaie un `POST` non idempotent et crée un doublon.
- Il appelle un service externe sans délai maximal : un fournisseur lent bloque tous les workers.
- En Spring, il lève une exception vérifiée dans un `@Transactional` et croit que la transaction est annulée : par défaut, elle ne l'est que pour les exceptions non vérifiées.
- En JavaScript, il lance une promesse sans `await` ni `catch` : l'erreur est perdue ou fait tomber le processus.
- Côté front, il n'affiche rien quand l'appel échoue, ou un message générique pour une erreur de validation qu'il pouvait placer sous le champ.

## Entrées
- Les conventions en place : exceptions métier existantes, gestionnaire global, format d'erreur d'API, composant d'erreur du front.
- Les dépendances de la zone qui peuvent échouer : base, API tierces, files, système de fichiers, saisie utilisateur.

## Procédure
1. **Classer chaque échec possible** du code écrit, et lui donner son traitement :

| Classe | Exemple | Traitement |
|--------|---------|------------|
| Validation | champ manquant | rejet à l'entrée, 422 avec erreurs par champ |
| Règle métier | stock insuffisant | exception métier typée, 409 ou 422, `type` stable |
| Absence | ressource inconnue ou d'un autre utilisateur | 404 |
| Droits | rôle insuffisant | 401 ou 403 selon le skill `api-contracts` |
| Panne transitoire | délai dépassé, 503, verrou mort | délai, nouvelle tentative bornée si idempotent, puis 503 |
| Bug | `null` inattendu, état impossible | ne pas attraper : laisser remonter au gestionnaire global, 500 générique |

2. **Exceptions métier typées**, une par cas que l'appelant doit distinguer (`InsufficientStockException`), dans le module métier, sans dépendance HTTP. Respecte la convention du projet si elle utilise des valeurs de retour (type `Result`, union discriminée) plutôt que des exceptions.
3. **Attraper seulement là où l'on sait quoi faire** : compenser, réessayer, traduire ou afficher. Sinon, laisser passer. Un `catch` qui traduit garde la cause : `new DomainException('…', previous: $e)` (PHP), `new ServiceException("…", e)` (Java), `new Error('…', { cause: err })` (TypeScript).
4. **Traduire en un seul point** les exceptions en réponses :
   - Laravel : méthode `render()` de l'exception, ou `->withExceptions(...)` dans `bootstrap/app.php` (Laravel 11 et plus) ;
   - Symfony : écouteur de `kernel.exception`, ou attribut `#[WithHttpStatus]` sur l'exception (Symfony 6.3 et plus) ;
   - Spring Boot : `@RestControllerAdvice` avec `@ExceptionHandler` renvoyant un `ProblemDetail` ;
   - Next.js : valeurs de retour pour les erreurs attendues des Server Actions et route handlers, `notFound()`, et `error.tsx` / `global-error.tsx` pour les imprévus.
5. **Message client sûr** : `title` et `detail` rédigés pour l'utilisateur ; trace, SQL et noms internes seulement dans les journaux, avec un identifiant de corrélation renvoyé au client. Mode debug désactivé hors développement (`APP_DEBUG`, `server.error.include-stacktrace=never`).
6. **Appels externes** : délai explicite sur chaque appel (`Http::timeout()` Laravel, option `timeout` du HttpClient Symfony, délais de connexion et de lecture du client Spring, `AbortSignal.timeout()` avec `fetch`). Nouvelle tentative seulement pour une panne transitoire et une opération idempotente : 3 essais au plus, attente croissante avec part aléatoire (`Http::retry()`, Spring Retry s'il est présent).
7. **Cohérence des données** : opération en plusieurs écritures dans une transaction (`DB::transaction`, `wrapInTransaction` Doctrine, `@Transactional(rollbackFor = Exception.class)` si une exception vérifiée doit annuler). Effet externe (e-mail, paiement) déclenché après validation de la transaction (`afterCommit` des jobs Laravel, `@TransactionalEventListener` Spring).
8. **Asynchrone** : chaque promesse est attendue ou reçoit un `catch` ; un job en file a un nombre d'essais, un délai et un traitement de l'échec définitif (`failed()` Laravel, transport d'échec Messenger) ; aucun échec définitif silencieux.
9. **Front et mobile** :
   - Angular : `HttpInterceptorFn` pour 401 et erreurs réseau, `ErrorHandler` global pour les imprévus ;
   - Next.js : `error.tsx` par segment ;
   - Expo Router : `export function ErrorBoundary` dans le fichier de route ;
   - toujours : erreurs de validation sous les champs, état d'erreur avec action « Réessayer » pour le réseau, saisie conservée après un échec.
10. **Journaliser une seule fois**, au point qui traite l'erreur (skill `logging`) : attendue en `warning` sans trace, bug en `error` avec trace.
11. **Tester les chemins d'échec** : un test par classe d'erreur produite, dont un test de panne de la dépendance externe simulée (`Http::fake()` avec 500 ou délai, `MockRestServiceServer`, MSW) qui vérifie l'état final des données.

## Livrable
Le code, ses tests d'échec, et dans le compte rendu :
```markdown
| Échec possible | Classe | Traitement | Réponse ou affichage | Test |
|----------------|--------|------------|----------------------|------|
| fournisseur de paiement en délai dépassé | transitoire | 2 nouvelles tentatives, puis commande `payment_pending` | 503 problem+json | `PaymentTest::timeout` |
```

## Vérifications
- `rg -n "catch\s*\([^)]*\)\s*\{\s*\}"` et équivalents ne trouvent aucun `catch` vide ajouté ; aucun `catch` générique hors du gestionnaire global.
- Chaque appel externe ajouté a un délai explicite, visible dans le diff.
- Chaque erreur métier a un test qui vérifie le statut, le `type` et l'absence de détail interne dans la réponse.

## Limites
- Les politiques de résilience lourdes (disjoncteur, file de reprise) relèvent de `architect`.
- L'alerte et la supervision en production sont hors du dépôt : signale-les à `devops-engineer`.

## En cas de blocage
- Comportement attendu en cas d'échec non spécifié (rembourser, réessayer plus tard, bloquer) : choisis l'option qui préserve les données et l'argent de l'utilisateur, consigne l'hypothèse et soumets-la à `product-analyst`.
- Gestion d'erreurs incohérente dans le projet : suis la convention majoritaire dans ta zone et ajoute l'harmonisation au plan.
