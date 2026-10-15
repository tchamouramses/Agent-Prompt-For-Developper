---
name: laravel
description: Savoir Laravel pour coder juste du premier coup - repérer la version et la structure du projet (avant ou après Laravel 11), utiliser les outils natifs, éviter les pièges Eloquent, files d'attente, transactions, configuration et autorisation. À utiliser pour toute tâche de code, de revue ou de débogage dans un projet Laravel.
---

# Laravel

La règle « outils natifs avant toute librairie » et les standards de base sont dans l'agent `laravel-implementer`. Ce skill donne ce que le modèle rate le plus souvent : la structure propre à chaque version et les pièges qui ne se voient qu'en production.

## Quand l'utiliser
- Toute tâche qui écrit, relit ou débogue du code dans un projet qui dépend de `laravel/framework`.
- Avant d'utiliser une API Laravel dont tu n'es pas sûr qu'elle existe dans la version installée.

## Ce que l'agent rate sans ce skill
- Il écrit pour une autre version : crée `app/Http/Kernel.php` ou `app/Console/Kernel.php` dans un projet Laravel 11 ou plus, ou cherche `bootstrap/app.php` configuré à la mode 11 dans un projet 10.
- Il suppose que `routes/api.php` existe (absent par défaut depuis Laravel 11).
- Il déclenche un job ou un événement dans une transaction, et le traitement part avant le commit, ou même si la transaction échoue.
- Il valide avec une Form Request dont `authorize()` renvoie `true` sans aucune Policy, ce qui laisse n'importe quel utilisateur connecté agir sur la ressource d'un autre.
- Il charge les relations dans une boucle (N+1), utilise `env()` hors de `config/`, ou fait confiance à `$request->all()`.

## Entrées
- `composer.json` et `composer.lock` (version de `laravel/framework`, contrainte `php`, paquets installés), `php artisan about`, la structure de `bootstrap/`, `routes/`, `app/`.

## Procédure

### 1. Situer le projet
1. Lis la version exacte : `composer show laravel/framework | head -5` ou `php artisan --version`. Note aussi les paquets qui changent la façon de coder : Livewire, Inertia, Filament, Sanctum, Passport, Horizon, Pest, Larastan.
2. Repère la structure selon la version :

| Élément | Laravel 10 et avant | Laravel 11 et après |
|---------|---------------------|---------------------|
| Middlewares, exceptions, routage | `app/Http/Kernel.php`, `app/Exceptions/Handler.php`, `RouteServiceProvider` | `bootstrap/app.php` (`withMiddleware`, `withExceptions`, `withRouting`) |
| Tâches planifiées | `app/Console/Kernel.php` | `routes/console.php` (`Schedule::`) |
| Routes d'API | `routes/api.php` présent | absent ; `php artisan install:api` l'ajoute avec Sanctum |
| Casts du modèle | propriété `$casts` | méthode `casts()` (la propriété reste acceptée) |
| Traductions | `lang/` présent | absent ; `php artisan lang:publish` |

3. Suis la structure du projet tel qu'il est, même s'il a été mis à jour sans adopter la nouvelle (un projet 11 peut garder ses anciens Kernel). Ne mélange pas les deux styles.
4. Pour toute autre API dont tu doutes, applique le skill `version-compatibility` : cherche-la dans `vendor/laravel/framework/src` avant de l'utiliser.

### 2. Outils d'inspection à utiliser avant de coder
- `php artisan route:list --path=<préfixe>` : routes, noms, middlewares et contrôleurs touchés.
- `php artisan model:show <Modèle>` : colonnes, casts, relations, observers.
- `php artisan about` et `php artisan config:show <fichier>` (fichiers sans secret seulement, skill `env-secrets`) : pilotes réels (cache, file, session, base).
- `php artisan event:list` : écouteurs déclenchés par un événement que tu modifies.

### 3. Pièges à éviter
- **Autorisation** : chaque action sur une ressource passe par une Policy (`$this->authorize()`, `Gate::authorize()`, middleware `can:`). Une Form Request ne renvoie `true` dans `authorize()` que si l'autorisation est faite ailleurs et testée. Les listes sont filtrées par propriétaire ou tenant dans la requête, pas après coup.
- **Données reçues** : utilise `$request->validated()` ou `$request->safe()`, jamais `$request->all()` pour écrire en base.
- **Transactions et effets** : un job, un événement ou un e-mail déclenché dans `DB::transaction` doit partir après le commit : `->afterCommit()` sur le job ou l'écouteur, ou `ShouldDispatchAfterCommit` / `ShouldQueueAfterCommit` selon la version. Vérifie la valeur de `after_commit` dans `config/queue.php`.
- **Concurrence** (méthode générale : skill `concurrency-control`) : une règle d'exclusivité (pas de chevauchement, stock) se protège dans `DB::transaction()` par `lockForUpdate()` sur la ligne parente (la salle, l'article) avant de vérifier puis d'écrire, ou par une contrainte unique dont la `QueryException` est traduite en 409. Sur SQLite, `lockForUpdate()` est sans effet : dans `config/database.php`, connexion `sqlite`, fixe `'transaction_mode' => 'IMMEDIATE'`, `'journal_mode' => 'WAL'` et `'busy_timeout' => 5000` (clés disponibles selon la version : vérifie-les dans la configuration du framework installé). `DB::transaction($callback, $tentatives)` rejoue sur interblocage.
- **Jobs** : `tries`, `backoff` et `timeout` explicites ; traitement idempotent (un job peut être rejoué) ; passer des identifiants ou des modèles (sérialisés par `SerializesModels`, rechargés à l'exécution), jamais des objets lourds ou des closures. `ShouldBeUnique` si deux exécutions simultanées posent problème.
- **Eloquent** : `with()` pour les relations lues dans une boucle ; `Model::preventLazyLoading(! app()->isProduction())` si le projet l'accepte ; `chunkById()` ou `lazyById()` pour parcourir beaucoup de lignes ; `withCount()` plutôt que `->relation->count()`. Les mises à jour en masse (`Model::query()->update()`) ne déclenchent ni événements ni observers : vérifie que rien n'en dépend.
- **Dates** : `now()` et `Carbon` sont mutables ; copie avec `->copy()` ou utilise `CarbonImmutable` si le projet l'a choisi. Stocke en UTC, convertis à l'affichage.
- **Configuration** : `env()` uniquement dans `config/*.php` (après `config:cache`, `env()` renvoie `null` ailleurs). Toute nouvelle variable va dans `.env.example` sans valeur réelle.
- **Liaison de route** : pour des ressources imbriquées (`/projets/{projet}/taches/{tache}`), `->scopeBindings()` empêche d'atteindre la tâche d'un autre projet.
- **Erreurs d'API** : sous `api/*`, toute erreur rend du JSON, même sans en-tête `Accept` : `->withExceptions(fn ($e) => $e->shouldRenderJsonWhen(fn ($request) => $request->is('api/*') || $request->expectsJson()))` dans `bootstrap/app.php`. Sinon un appel non authentifié tente une redirection vers la route `login`, absente d'une API, et renvoie 500 au lieu de 401. Un test l'appelle sans `Accept`.
- **API Resources** : `whenLoaded()` pour les relations, `whenCounted()` pour les compteurs ; pagination avec `->paginate()` renvoyée telle quelle à la Resource pour garder les métadonnées.
- **Cache** : clé qui inclut tout ce qui fait varier la valeur (utilisateur, tenant, langue) ; invalidation prévue au même endroit que l'écriture.

### 4. Générer et nettoyer
- Génère avec `php artisan make:*` (le modèle avec `-mfs` si migration, factory et seeder sont utiles), puis supprime les méthodes générées vides que tu n'utilises pas.
- Après une suppression, retire aussi la route, la vue, la traduction, la Policy, le test et la factory devenus inutiles (principes de code, zéro code mort).

### 5. Internationalisation (projet multilingue)
Règles communes, contrôles et livrable : skill `i18n`. Spécifique à Laravel :
- Textes par `__('checkout.total')` ou `@lang` dans Blade, pluriels par `trans_choice('cart.items', $n, ['count' => $n])` (`{0} …|{1} …|[2,*] …`) ; clés courtes groupées dans `lang/<langue>/<domaine>.php`, ou phrases en clés dans `lang/<langue>.json` : une seule convention par projet. Variables `:name`, jamais de concaténation.
- Messages de validation : `lang/<langue>/validation.php` (`custom` et `attributes`) publié pour chaque langue (`php artisan lang:publish` en Laravel 11+) ; Form Requests sans message en dur (`messages()` renvoie des appels à `__()`).
- Langue de la requête fixée par un middleware (`App::setLocale()`) selon l'ordre du skill `i18n` ; `fallback_locale` défini ; mails et notifications envoyés dans la langue du destinataire (`Mail::to($user)->locale($user->locale)` ou `HasLocalePreference` sur le modèle), y compris en file d'attente.
- Formats : `Carbon::translatedFormat()` et `isoFormat()` avec la langue active ; `Number::format()`, `Number::currency()` (extension `intl`).
- Front Inertia ou SPA : les clés envoyées au client passent par l'outil du front, pas par une copie manuelle des fichiers PHP. Parité : convertis les fichiers en JSON (commande du skill `i18n`) puis lance le script de parité.

## Livrable
Le code de la tâche conforme à la structure de la version installée, et dans le compte rendu : la version de Laravel relevée, les commandes d'inspection lancées, les pièges vérifiés qui s'appliquaient à la tâche.

## Vérifications
- `php artisan route:list` ne montre aucune route orpheline ni contrôleur manquant.
- Les tests de la zone passent (`php artisan test` ou `./vendor/bin/pest`), ainsi que Pint et Larastan s'ils sont présents.
- Aucune requête dans une boucle sur les écrans ou les routes touchés (vérifié par un test, `preventLazyLoading` ou le journal des requêtes).

## Limites
- Les paquets de l'écosystème (Livewire, Filament, Inertia, Horizon) ont leurs propres versions : lis leur version dans `composer.lock` avant d'utiliser leurs API.
- Les tests : skill `testing-php`. La sécurité détaillée : skill `security-php`. Le style : skill `coding-conventions-php`, et ses outils : skill `lint-format-php`. Le schéma : skill `migrations`. La montée de version : skill `upgrade-laravel`.

## En cas de blocage
- API introuvable dans `vendor/` : elle n'existe pas dans cette version ; utilise l'équivalent de la version installée et consigne-le.
- Le projet mélange déjà les deux structures : suis celle des fichiers les plus récents et signale l'incohérence dans le compte rendu, sans la corriger hors de ta tâche.
