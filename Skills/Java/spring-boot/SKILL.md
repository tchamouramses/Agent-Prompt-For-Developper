---
name: spring-boot
description: Savoir Spring Boot pour coder juste du premier coup - repérer les versions (Spring Boot 2, 3 ou 4, Java, Jakarta ou javax), utiliser les outils d'inspection, éviter les pièges des transactions, de JPA, de Spring Security, de la configuration et des clients HTTP. À utiliser pour toute tâche de code, de revue ou de débogage dans un projet Spring Boot.
---

# Spring Boot

Les standards de base (injection par constructeur, DTO en records, `ProblemDetail`) sont dans l'agent `spring-boot-implementer`. Ce skill donne ce que le modèle rate le plus souvent : ce qui change entre les générations de Spring Boot, et les pièges qui ne se voient qu'en production.

## Quand l'utiliser
- Toute tâche qui écrit, relit ou débogue du code dans un projet qui dépend de `org.springframework.boot`.
- Avant d'utiliser une API Spring dont tu n'es pas sûr qu'elle existe dans la version installée.

## Ce que l'agent rate sans ce skill
- Il importe `javax.persistence` ou `javax.validation` dans un projet Spring Boot 3 ou plus (Jakarta EE : `jakarta.*`), ou l'inverse.
- Il écrit un `WebSecurityConfigurerAdapter`, `antMatchers()` ou `@EnableGlobalMethodSecurity`, retirés de Spring Security 6.
- Il met `@Transactional` sur une méthode privée ou l'appelle depuis la même classe : le proxy ne s'applique pas et la transaction n'existe pas.
- Il laisse `spring.jpa.open-in-view` à sa valeur par défaut et charge des relations paresseuses pendant le rendu de la réponse (requêtes cachées, N+1).
- Il utilise `@MockBean`, déprécié depuis Spring Boot 3.4, au lieu de `@MockitoBean`.
- Il expose tous les endpoints Actuator, ou laisse la console H2 active hors développement.

## Entrées
- `pom.xml` ou `build.gradle(.kts)` (parent ou plugin `org.springframework.boot` et sa version, `java.version` ou toolchain, starters), `src/main/resources/application*.yml|properties`, la classe `@SpringBootApplication`.

## Procédure

### 1. Situer le projet
1. Versions exactes : `./mvnw help:evaluate -Dexpression=project.parent.version -q -DforceStdout` (ou la version du plugin Gradle), version de Java (`java -version`, toolchain), outil de migration (Flyway ou Liquibase).
2. Repère ce qui dépend de la génération :

| Élément | Spring Boot 2.x | Spring Boot 3.x | Spring Boot 4.x |
|---------|-----------------|-----------------|-----------------|
| Java minimal | 8 | 17 | 17 |
| Paquets Java EE | `javax.*` | `jakarta.*` | `jakarta.*` |
| Sécurité | `WebSecurityConfigurerAdapter` possible | bean `SecurityFilterChain`, `requestMatchers()`, `@EnableMethodSecurity` | idem |
| Client HTTP | `RestTemplate`, `WebClient` | `RestClient` (3.2+), interfaces `@HttpExchange` | idem |
| Simulation dans les tests | `@MockBean` | `@MockitoBean` (3.4+, `@MockBean` déprécié) | `@MockitoBean` |
| Jackson | 2.x | 2.x | 3.x (paquets `tools.jackson`), lire le guide de migration |

3. Pour toute autre API dont tu doutes, applique le skill `version-compatibility` : cherche la classe dans les dépendances résolues (`./mvnw dependency:tree`, `./gradlew dependencies`) et la documentation de référence de la version installée.

### 2. Outils d'inspection avant de coder
- `./mvnw dependency:tree -Dincludes=<groupe>` ou `./gradlew dependencyInsight --dependency <nom>` : version réellement résolue d'une dépendance.
- Lancement avec `--debug` : rapport des auto-configurations appliquées ou écartées (pourquoi un bean existe ou non).
- Actuator en local, s'il est présent : `/actuator/mappings` (routes), `/actuator/beans`, `/actuator/configprops`, `/actuator/conditions`.
- `@SpringBootTest` qui démarre : premier test à lancer quand la configuration change.

### 3. Pièges à éviter
- **Concurrence** (méthode générale : skill `concurrency-control`) : règle d'exclusivité protégée dans une méthode `@Transactional` par un verrou sur l'entité parente (`@Lock(LockModeType.PESSIMISTIC_WRITE)` sur la méthode du repository qui la charge), ou par une contrainte unique dont la `DataIntegrityViolationException` est traduite en 409 ; version optimiste avec `@Version` et `ObjectOptimisticLockingFailureException`. H2 ne reproduit pas les verrous du moteur de production : prouve-les avec Testcontainers.
- **Transactions** : `@Transactional` sur des méthodes publiques de beans Spring, appelées depuis un autre bean (pas d'appel interne). Une exception vérifiée n'annule pas la transaction par défaut : déclare `rollbackFor` ou utilise des exceptions non vérifiées. Un événement ou un message produit dans la transaction part après le commit : `@TransactionalEventListener(phase = AFTER_COMMIT)` (skill `background-jobs-events`).
- **JPA** : `spring.jpa.open-in-view=false` ; relations paresseuses chargées dans le service par `JOIN FETCH` ou `@EntityGraph` ; pagination avec `Pageable` (jamais `JOIN FETCH` d'une collection avec pagination : Hibernate pagine en mémoire). Pas de `@Data` Lombok sur une entité (`equals`/`hashCode`/`toString` sur les relations : boucles et chargements). `ddl-auto` à `validate` ou `none` dès que Flyway ou Liquibase gère le schéma.
- **Requêtes** : paramètres nommés dans `@Query` et les requêtes natives, jamais de concaténation.
- **Validation** : `@Valid` sur le corps et `@Validated` sur la classe pour valider les paramètres de chemin et de requête ; un DTO dédié par entrée, jamais l'entité liée à la requête.
- **Sécurité** : chaîne de filtres explicite ; CSRF désactivé seulement pour une API sans état authentifiée par jeton, jamais pour une application à session ; autorisation sur la ressource précise (propriétaire, tenant), pas seulement le rôle (skill `security-java`).
- **Actuator et outils** : en production, n'exposer que `health` et `info` (ou ce que la spec demande), derrière l'authentification ; console H2 et `spring-boot-devtools` absents du profil de production.
- **Configuration** : `@ConfigurationProperties` (records) validées avec `@Validated` plutôt que `@Value` dispersés ; secrets fournis par l'environnement, jamais dans `application.yml` versionné. Toute nouvelle propriété est documentée avec une valeur d'exemple.
- **Clients HTTP** : délais de connexion et de lecture explicites ; erreurs du tiers converties en exceptions métier.
- **Threads virtuels** (Java 21, `spring.threads.virtual.enabled`) : pas de `synchronized` autour d'appels bloquants longs avant Java 24 (épinglage du thread).

### 4. Générer et nettoyer
- Après une suppression, retire aussi les beans, propriétés de configuration, migrations non appliquées, DTO, tests et dépendances devenus inutiles.
- Formatage et analyse statique : skill `lint-format-java`. Montée de version de Spring Boot : skill `upgrade-spring-boot`.

### 5. Internationalisation (projet multilingue)
Règles communes, contrôles et livrable : skill `i18n`. Spécifique à Spring Boot :
- `MessageSource` auto-configuré : `spring.messages.basename` (`messages`, ou plusieurs bases séparées par des virgules), `spring.messages.encoding=UTF-8`, `spring.messages.fallback-to-system-locale=false` pour que le repli soit `messages.properties` et pas la langue du serveur. Variables positionnelles `{0}` ; pluriels et choix par `{0,choice,0#…|1#…|1<…}` ou ICU4J si le projet l'a adopté.
- Langue par `LocaleResolver` : `AcceptHeaderLocaleResolver` (API sans état, langues supportées déclarées) ou `CookieLocaleResolver` avec `LocaleChangeInterceptor` (application à session) ; `LocaleContextHolder.getLocale()` dans le code de service, jamais `Locale.getDefault()`.
- Validation : messages de Bean Validation en clés (`{order.quantity.min}`) résolus par le `MessageSource` (`LocalValidatorFactoryBean` lié au `MessageSource`) ; erreurs d'API renvoyées avec un code stable et le message traduit (`ProblemDetail`, skill `error-handling`).
- E-mails et documents dans la langue du destinataire (langue stockée sur l'utilisateur, passée au moteur de templates : Thymeleaf `#messages`, contexte `Locale`).
- Formats : `DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM).withLocale(locale)`, `NumberFormat.getCurrencyInstance(locale)`. Parité des fichiers `messages_<langue>.properties` : script du skill `i18n`.

## Livrable
Le code de la tâche conforme à la génération installée, et dans le compte rendu : versions de Spring Boot et de Java relevées, outils d'inspection utilisés, pièges vérifiés qui s'appliquaient.

## Vérifications
- `./mvnw verify` ou `./gradlew check` passe (tests, formatage et analyse statique configurés).
- L'application démarre (test `@SpringBootTest` de contexte, ou `spring-boot:run` / `bootRun` sur le profil de test).
- Aucune requête paresseuse déclenchée hors transaction (pas de `LazyInitializationException`, `open-in-view` à `false`).

## Limites
- Les tests : skill `testing-java`. La sécurité détaillée : skill `security-java`. Le style : skill `coding-conventions-java`. Le schéma : skill `migrations`.
- Spring Cloud, Spring Batch et Spring Modulith ont leurs propres versions, alignées sur une génération de Spring Boot : lis leur version avant d'utiliser leurs API.

## En cas de blocage
- Classe introuvable dans les dépendances : elle n'existe pas dans cette version ; utilise l'équivalent installé et consigne-le.
- Contexte Spring qui ne démarre pas : lis le rapport de conditions (`--debug`) et la première cause de la pile, pas la dernière ligne.
