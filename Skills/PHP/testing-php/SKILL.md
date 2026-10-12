---
name: testing-php
description: Écrire et lancer des tests PHP fiables avec les outils du projet (Pest ou PHPUnit, Laravel ou Symfony) - choisir la bonne isolation de base, simuler seulement les frontières, utiliser les assertions adaptées et produire une preuve d'exécution. À utiliser pour écrire, corriger ou juger des tests dans un projet PHP.
---

# Tests PHP

Le choix des tests (niveau, cas, fiabilité) est dans le skill `testing-strategy`. Ce skill dit comment le faire avec l'outillage PHP.

## Quand l'utiliser
- Écrire ou corriger des tests dans un projet PHP (Laravel, Symfony ou PHP pur).
- Relire des tests PHP (`code-reviewer`, `quality-gatekeeper`).

## Ce que l'agent rate sans ce skill
- Il écrit du PHPUnit dans un projet Pest, ou des annotations `@test` et `@dataProvider`, dépréciées depuis PHPUnit 10 et retirées en 12.
- Il teste sur SQLite en mémoire une requête qui dépend de MySQL ou PostgreSQL (JSON, recherche, contraintes, tri sensible à la casse) : le test passe, la production casse.
- Il simule Eloquent, Doctrine ou un service du projet au lieu de laisser la base de test répondre.
- Il utilise `Event::fake()` sans liste et coupe sans le voir les observers et écouteurs dont le test dépend.
- Il déclare « les tests passent » d'après une sortie tronquée ou sans avoir lancé la commande.

## Entrées
- `composer.json` (`pestphp/pest`, `phpunit/phpunit`, `symfony/test-pack`, `zenstruck/foundry`, `dama/doctrine-test-bundle`), `phpunit.xml` ou `phpunit.xml.dist`, `tests/Pest.php`, quelques tests existants de la même zone.

## Procédure
1. **Suivre l'outil du projet.** Pest si `tests/Pest.php` existe, sinon PHPUnit ; copie la forme des tests voisins (fonctions `it()` ou `test()`, classes, traits, helpers). PHPUnit 10 et plus : attributs `#[Test]`, `#[DataProvider('cas')]` avec un fournisseur `public static`.
2. **Choisir l'isolation de base** :
   - Laravel : `RefreshDatabase` (ou `LazilyRefreshDatabase`) par défaut ; `DatabaseTransactions` seulement si la base est déjà migrée et partagée.
   - Symfony : `dama/doctrine-test-bundle` (transaction annulée après chaque test) s'il est installé ; sinon réinitialisation explicite du schéma.
   - Relis `phpunit.xml` : `DB_CONNECTION` et `DB_DATABASE` de test. Si une requête testée dépend du moteur, le test doit tourner sur le même moteur que la production ; sinon, signale-le comme **non vérifié** pour ce moteur.
3. **Créer les données dans le test** avec les factories (Laravel) ou Foundry et les fixtures du projet (Symfony), avec des états nommés (`->admin()`, `->expired()`) plutôt que des tableaux recopiés.
4. **Simuler seulement les frontières** :
   - Laravel : `Http::fake()` avec `Http::preventStrayRequests()`, `Mail::fake()`, `Notification::fake()`, `Queue::fake()` ou `Bus::fake()`, `Storage::fake()`, `Event::fake([ÉvénementPrécis::class])` (toujours avec la liste), `$this->freezeTime()` ou `$this->travelTo()`.
   - Symfony : `MockHttpClient` ou `MockResponse`, transport `in-memory` pour Messenger, `ClockMock` ou `MockClock`, mailer de test avec `assertEmailCount()`.
   - Jamais de simulation d'un modèle, d'un repository ou d'un service du projet quand un test d'intégration peut l'exercer.
5. **Tester le comportement par la porte d'entrée** :
   - Laravel : `actingAs($user)` puis `getJson()`, `postJson()` ; `assertStatus()`, `assertJsonPath()`, `assertJson(fn (AssertableJson $json) => ...)`, `assertDatabaseHas()`, `assertForbidden()`, `assertUnprocessable()` avec `assertJsonValidationErrors()`.
   - Symfony : `static::createClient()`, `loginUser()`, `request()`, `assertResponseStatusCodeSame()`, `assertSelectorTextContains()`, `assertJsonContains()` si API Platform.
   - Pour chaque route touchée : cas nominal, non connecté, rôle insuffisant, ressource d'un autre utilisateur, données invalides.
6. **Lancer et prouver** :
   - zone : `php artisan test --filter=NomDuTest` ou `./vendor/bin/pest tests/Feature/Notes`, `./vendor/bin/phpunit --filter NomDuTest` ;
   - suite complète : `php artisan test` (ajoute `--parallel` si `brianium/paratest` est installé), `./vendor/bin/phpunit` ;
   - cite la ligne de résumé exacte (`Tests: 42 passed (118 assertions)`), pas une interprétation.
7. **Concurrence** : une règle d'exclusivité (skill `concurrency-control`) se prouve en conditions réelles, pas par deux appels successifs dans un test :
   - base dédiée (`DB_DATABASE` vers un fichier temporaire ou une base de test), `php artisan migrate:fresh --seed --force` (Laravel) ou `bin/console doctrine:migrations:migrate -n` (Symfony) ;
   - serveur à plusieurs workers : `PHP_CLI_SERVER_WORKERS=8 php artisan serve --port=<port>` (Laravel) ou `PHP_CLI_SERVER_WORKERS=8 php -S 127.0.0.1:<port> -t public` (Symfony) ;
   - au moins 3 rafales de 20 requêtes parallèles (`xargs -P 20 curl …`, ou un script) avec des jetons d'utilisateurs différents, puis comptage des statuts (succès, 409, 5xx) et requête de contrôle des lignes en violation ;
   - le script est versionné (par exemple `tests/Concurrency/`) et sa commande citée ; s'il ne peut pas tourner en CI, il est cité dans le compte rendu avec son dernier résultat.
8. **Couverture** si demandée : `XDEBUG_MODE=coverage php artisan test --coverage --min=<seuil>` ou `--coverage-text` avec PCOV ; sans pilote de couverture, marque la couverture **non vérifiée**.

## Livrable
Les tests, la commande lancée et sa ligne de résumé, et la correspondance critère ou règle → test (skill `testing-strategy`).

## Vérifications
- Chaque nouveau test a été vu en échec puis en succès quand c'est possible.
- Aucun `markTestSkipped()`, `->skip()`, `->todo()` ou assertion retirée pour faire passer la suite.
- Les tests passent aussi lancés seuls et dans un ordre différent (`--order-by=random` avec PHPUnit, `--random-order-seed` selon la version, ou relance du fichier seul).

## Limites
- N'installe pas de nouvel outil de test si le projet en a un pour ce niveau (règle 4 des principes communs). Les tests de navigateur relèvent de `e2e-validator`.

## En cas de blocage
- Base de test du bon moteur indisponible : lance les tests sur ce qui existe, marque les requêtes dépendantes du moteur **non vérifiées**, et propose dans le compte rendu le service de base à ajouter en CI.
- Test existant rouge avant ta modification : note-le comme état de départ, ne le corrige pas en silence ; `debugger` s'il bloque ta tâche.
