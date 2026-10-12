---
name: testing-java
description: Écrire et lancer des tests Java fiables avec les outils du projet (JUnit Jupiter, AssertJ, Mockito, tests de tranche Spring, Testcontainers) - choisir le bon niveau, garder le contexte Spring en cache, simuler seulement les frontières et produire une preuve d'exécution Maven ou Gradle. À utiliser pour écrire, corriger ou juger des tests dans un projet Java.
---

# Tests Java

Le choix des tests (niveau, cas, fiabilité) est dans le skill `testing-strategy`. Ce skill dit comment le faire avec l'outillage Java et Spring.

## Quand l'utiliser
- Écrire ou corriger des tests dans un projet Java, Spring Boot ou non.
- Relire des tests Java (`code-reviewer`, `quality-gatekeeper`).

## Ce que l'agent rate sans ce skill
- Il écrit du JUnit 4 (`org.junit.Test`, `@RunWith`) dans un projet JUnit Jupiter, ou l'inverse.
- Il démarre `@SpringBootTest` pour tester une méthode de service, et la suite devient lente.
- Il multiplie les combinaisons de `@MockitoBean` ou les `@DirtiesContext` : chaque classe recrée le contexte Spring.
- Il teste un repository sur H2 alors que la production utilise PostgreSQL ou MySQL : requêtes natives, types et contraintes divergent.
- Il attend un traitement asynchrone avec `Thread.sleep()`.
- Il affirme que les tests passent sans citer le résumé Surefire ou Gradle.

## Entrées
- `pom.xml` ou `build.gradle(.kts)` (`spring-boot-starter-test`, `junit-jupiter`, `mockito`, `assertj`, `testcontainers`, `spring-security-test`, plugins Surefire et Failsafe), `src/test/`, tests voisins.

## Procédure
1. **Suivre l'outillage du projet.** JUnit Jupiter (`org.junit.jupiter.api.Test`) et AssertJ (`assertThat`) fournis par `spring-boot-starter-test` ; copie la forme des tests voisins (nommage, `@DisplayName`, `@Nested`, méthodes utilitaires). Tests paramétrés avec `@ParameterizedTest` et `@CsvSource` ou `@MethodSource`.
2. **Choisir le niveau** :
   - logique pure (domaine, service sans infrastructure) : test unitaire sans Spring, dépendances simulées avec Mockito (`@ExtendWith(MockitoExtension.class)`, `@Mock`, `@InjectMocks`) ;
   - couche web : `@WebMvcTest(MonController.class)` avec `MockMvc` (ou `MockMvcTester` à partir de Spring Framework 6.2) et les services simulés par `@MockitoBean` ;
   - persistance : `@DataJpaTest` ; avec Testcontainers, `@AutoConfigureTestDatabase(replace = Replace.NONE)` pour garder la vraie base ;
   - intégration complète : `@SpringBootTest` (avec `webEnvironment = RANDOM_PORT` et `RestClient` ou `TestRestTemplate` pour un appel HTTP réel), réservé aux parcours.
3. **Base de test réaliste** : Testcontainers avec le même moteur et la même version majeure que la production (`@Testcontainers`, `@Container`, et `@ServiceConnection` à partir de Spring Boot 3.1). Sans Docker disponible, marque les requêtes dépendantes du moteur **non vérifiées**.
4. **Garder le contexte en cache** : mêmes classes de configuration, mêmes propriétés et même jeu de `@MockitoBean` pour les tests d'intégration ; une classe de base commune si le projet en a une ; pas de `@DirtiesContext` sauf état global réellement modifié.
5. **Simuler seulement les frontières** : client HTTP d'un tiers (`MockRestServiceServer`, WireMock si présent), horloge (`Clock` injecté), envoi d'e-mails. Jamais de simulation d'un repository dans un test dont le but est la requête.
6. **Sécurité** : `spring-security-test` ; `@WithMockUser` ou `with(user(...))`, `with(jwt())` pour une API à jetons, `with(csrf())` pour une application à session. Pour chaque route touchée : non authentifié, rôle insuffisant, ressource d'un autre utilisateur, données invalides.
7. **Asynchrone** : Awaitility (`await().atMost(...).untilAsserted(...)`) si présent, ou exécution synchrone du traitement dans le test ; jamais `Thread.sleep()`.
8. **Lancer et prouver** :
   - un test : `./mvnw test -Dtest=NomTest#methode` ou `./gradlew test --tests 'com.exemple.NomTest.methode'` ;
   - suite : `./mvnw verify` (inclut les tests d'intégration Failsafe `*IT`) ou `./gradlew check` ;
   - cite le résumé exact (`Tests run: 48, Failures: 0, Errors: 0, Skipped: 0`) ou la ligne Gradle, pas une interprétation.
9. **Concurrence** : une règle d'exclusivité (skill `concurrency-control`) se prouve sur le vrai moteur (Testcontainers) par un test `@SpringBootTest(webEnvironment = RANDOM_PORT)` qui lance au moins 20 appels HTTP simultanés (`ExecutorService` et `CountDownLatch` pour un départ commun), sur plusieurs rafales ; il vérifie le nombre de succès, l'absence de 5xx et l'absence de ligne en violation en base.
10. **Couverture** si demandée : JaCoCo s'il est configuré (`./mvnw verify` puis `target/site/jacoco/index.html`) ; sinon **non vérifiée**.

## Livrable
Les tests, la commande lancée et son résumé, et la correspondance critère ou règle → test (skill `testing-strategy`).

## Vérifications
- Chaque nouveau test a été vu en échec puis en succès quand c'est possible.
- Aucun `@Disabled`, `assumeTrue` ajouté ou assertion retirée pour faire passer la suite.
- Le nombre de démarrages du contexte Spring n'a pas augmenté sans raison (journal « Started … in » une fois par configuration).

## Limites
- N'ajoute pas de librairie de test si le projet en a une pour ce besoin (règle 4 des principes communs). Les tests de navigateur relèvent de `e2e-validator`.

## En cas de blocage
- Docker indisponible pour Testcontainers : lance ce qui peut tourner, marque le reste **non vérifié**, et indique la commande à lancer en CI.
- Test existant rouge avant ta modification : note-le comme état de départ ; `debugger` s'il bloque ta tâche.
