---
name: symfony
description: Savoir Symfony pour coder juste du premier coup - repérer la version et les choix du projet (Flex, API Platform, Twig ou front séparé), utiliser les commandes d'inspection, éviter les pièges Doctrine, Messenger, sérialisation, sécurité et configuration. À utiliser pour toute tâche de code, de revue ou de débogage dans un projet Symfony.
---

# Symfony

Les standards de base (injection par constructeur, contrôleurs fins, Voters) sont dans l'agent `symfony-implementer`. Ce skill donne ce que le modèle rate le plus souvent : ce qui change selon la version, et les pièges qui ne se voient qu'en production.

## Quand l'utiliser
- Toute tâche qui écrit, relit ou débogue du code dans un projet qui dépend de `symfony/framework-bundle`.
- Avant d'utiliser une API Symfony ou Doctrine dont tu n'es pas sûr qu'elle existe dans la version installée.

## Ce que l'agent rate sans ce skill
- Il écrit des annotations Doctrine (`@ORM\Column`) ou des `@Route` en docblock, retirées de Doctrine ORM 3 et de Symfony 7, au lieu des attributs PHP.
- Il utilise `SensioFrameworkExtraBundle` (`@ParamConverter`, `@Security`), abandonné, au lieu de `#[MapEntity]` et `#[IsGranted]` du cœur.
- Il expose une entité Doctrine entière par le Serializer ou API Platform, champs internes et relations compris.
- Il dispatche un message Messenger vers un transport externe avant le `flush()` : le handler lit une donnée absente.
- Il appelle `flush()` dans une boucle, ou laisse Twig charger les relations une par une (N+1).
- Il lit `$_ENV` ou `getenv()` dans le code au lieu de paramètres injectés, ou met un secret dans `.env` versionné.

## Entrées
- `composer.json` et `composer.lock` (`symfony/framework-bundle`, `doctrine/orm`, `api-platform/core`, `symfony/messenger`, `symfony/ux-*`, `symfony/asset-mapper` ou `symfony/webpack-encore-bundle`), `symfony.lock`, `config/`, `bin/console about`.

## Procédure

### 1. Situer le projet
1. Version exacte : `bin/console about` ou `composer show symfony/framework-bundle | head -5`. Note aussi Doctrine ORM (2 ou 3), API Platform, la solution front (Twig + AssetMapper ou Encore, Symfony UX, ou front séparé).
2. Repère ce qui dépend de la version :

| Élément | Symfony 5.4 / Doctrine ORM 2 | Symfony 6.4, 7.x et 8.x / Doctrine ORM 3 |
|---------|------------------------------|-------------------------------------|
| Routes et mapping | annotations encore possibles | attributs PHP (`#[Route]`, `#[ORM\Column]`) ; annotations retirées en Symfony 7 et ORM 3 |
| Résolution d'entité | `@ParamConverter` (bundle Sensio) | `#[MapEntity]` (6.2+) |
| Entrées d'API | désérialisation manuelle | `#[MapRequestPayload]`, `#[MapQueryString]` (6.3+) |
| Autorisation | `@Security` / `@IsGranted` du bundle Sensio | `#[IsGranted]` du cœur (6.2+) |
| Tâches planifiées | cron + commande | composant Scheduler (6.3+) si installé |
| Assets | Webpack Encore | AssetMapper par défaut des nouveaux projets (6.3+) |

3. Pour toute autre API dont tu doutes, applique le skill `version-compatibility` : cherche-la dans `vendor/symfony/` ou `vendor/doctrine/` avant de l'utiliser. Les dépréciations actives : `bin/console debug:container --deprecations`.

### 2. Commandes d'inspection avant de coder
- `bin/console debug:router <nom>` et `debug:router --show-controllers` : routes touchées.
- `bin/console debug:autowiring <mot>` : services injectables ; `debug:container <service>` : définition réelle.
- `bin/console debug:config <bundle>` : configuration effective (sécurité, Messenger, Doctrine).
- `bin/console debug:messenger` : messages et handlers ; `debug:event-dispatcher <événement>` : écouteurs.
- `bin/console doctrine:schema:validate` : mapping cohérent avec la base de test.

### 3. Pièges à éviter
- **Doctrine** : une entité chargée est suivie, `persist()` ne sert qu'aux nouvelles ; un seul `flush()` par cas d'usage, jamais dans une boucle. Gros volumes : `toIterable()` et `clear()` par lots. Relations lues dans une boucle ou un template : jointure avec `addSelect()` dans le repository. Paramètres toujours liés (`setParameter`), jamais concaténés dans le DQL.
- **Migrations** : `doctrine:migrations:diff` génère tout l'écart du mapping, y compris des changements qui ne sont pas les tiens ; relis et retire ce qui n'appartient pas à la tâche. Jamais `doctrine:schema:update --force` (skill `migrations`).
- **Sérialisation** : jamais d'entité exposée telle quelle. DTO de sortie, ou groupes de sérialisation explicites (`#[Groups]`) ; en API Platform, `normalizationContext` et `denormalizationContext` par opération, et `security` par opération.
- **Entrées** : DTO validé par `#[MapRequestPayload]` (erreur 422 automatique) ; jamais `$request->request->all()` écrit directement dans une entité.
- **Concurrence** (méthode générale : skill `concurrency-control`) : règle d'exclusivité protégée dans `$em->wrapInTransaction()` par un verrou sur l'entité parente (`$em->find(Salle::class, $id, LockMode::PESSIMISTIC_WRITE)` ou `->setLockMode(LockMode::PESSIMISTIC_WRITE)` sur la requête), ou par une contrainte unique dont l'`UniqueConstraintViolationException` est traduite en 409 ; version optimiste avec `#[ORM\Version]` et `OptimisticLockException`. Sur SQLite, le verrou de ligne n'existe pas : préfère le même moteur que la production pour ces tests.
- **Messenger** : messages simples (identifiants, pas d'entités), handlers idempotents (skill `background-jobs-events`). Avec le transport Doctrine sur la même connexion, l'envoi fait partie de la transaction ; avec un transport externe (AMQP, Redis), dispatche après le `flush()`, ou depuis un handler avec `DispatchAfterCurrentBusStamp`. Fixe `retry_strategy` et un transport `failed`.
- **Sécurité** : chaque route protégée par `#[IsGranted]`, `access_control` ou un Voter ; un Voter vérifie la ressource précise, pas seulement le rôle. Les formulaires gardent la protection CSRF.
- **Twig** : l'échappement automatique protège ; `|raw` seulement sur un contenu assaini côté serveur, et justifié.
- **Configuration** : paramètres injectés (`%env(...)%` dans `config/services.yaml` ou `#[Autowire(env: ...)]`) ; secrets dans le coffre (`secrets:set`) ou l'environnement, jamais dans `.env` versionné (seul `.env.local`, ignoré, contient des valeurs locales). Toute nouvelle variable va dans `.env` avec une valeur factice.
- **Services** : sans état ; aucune donnée de requête stockée dans une propriété d'un service partagé (fuite entre requêtes avec un runtime persistant comme FrankenPHP en mode worker).

### 4. Générer et nettoyer
- Génère avec `bin/console make:*` si MakerBundle est installé, puis supprime les méthodes générées inutiles.
- Après une suppression, retire aussi la route, le template, la traduction, le Voter, le test, la fixture et la configuration devenus inutiles.

### 5. Internationalisation (projet multilingue)
Règles communes, contrôles et livrable : skill `i18n`. Spécifique à Symfony :
- Composant Translation : `{{ 'checkout.total'|trans }}` ou `{% trans %}` dans Twig, `TranslatorInterface::trans()` dans le code, `TranslatableMessage` (`t()`) pour un message construit hors de la requête ; fichiers `translations/<domaine>+intl-icu.<langue>.xlf` (ou `.yaml`) pour les pluriels et choix ICU ; un domaine par usage (`messages`, `validators`, `security`, `emails`).
- Contraintes de validation : messages sous forme de clés traduites dans le domaine `validators`.
- Langue : `framework.default_locale` et `framework.enabled_locales`, `{_locale}` dans les routes (avec `requirements`) ou résolution par un écouteur selon l'ordre du skill `i18n` ; `framework.translator.fallbacks` défini. E-mails rendus dans la langue du destinataire (`locale` du `TemplatedEmail` ou `LocaleSwitcher::runWithLocale()`).
- Formats Twig : filtres `format_date`, `format_datetime`, `format_currency`, `format_number` (`twig/intl-extra`) avec la langue active.
- Contrôles : `bin/console debug:translation <langue> --only-missing` et `--only-unused` pour chaque langue, `bin/console translation:extract --dump-messages <langue>` pour voir les clés non extraites, `bin/console lint:xliff translations` ou `lint:yaml translations`.

## Livrable
Le code de la tâche conforme à la version installée, et dans le compte rendu : versions de Symfony et Doctrine relevées, commandes d'inspection lancées, pièges vérifiés qui s'appliquaient.

## Vérifications
- `bin/console lint:container`, `lint:yaml config`, `lint:twig templates` (si Twig) passent.
- `bin/console doctrine:schema:validate` passe sur la base de test après migration.
- Les tests de la zone passent (`bin/phpunit` ou `vendor/bin/phpunit`), ainsi que PHPStan et PHP-CS-Fixer s'ils sont configurés.

## Limites
- Les tests : skill `testing-php`. La sécurité détaillée : skill `security-php`. Le style : skill `coding-conventions-php`, et ses outils : skill `lint-format-php`. Le schéma : skill `migrations`. La montée de version : skill `upgrade-symfony`.
- API Platform et les composants Symfony UX ont leurs propres versions : lis-les dans `composer.lock` avant d'utiliser leurs API.

## En cas de blocage
- API introuvable dans `vendor/` : elle n'existe pas dans cette version ; utilise l'équivalent installé et consigne-le.
- Le projet mélange annotations et attributs : suis le style des fichiers que tu modifies, et signale la migration à faire comme tâche du plan.
