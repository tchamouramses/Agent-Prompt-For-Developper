---
name: upgrade-spring-boot
description: Monter de version un projet Spring Boot (mineure ou majeure, dont 2 vers 3 et 3 vers 4) en sécurité - lire les guides de migration officiels, passer par la dernière mineure, traiter Java, Jakarta, Spring Security, Hibernate et les propriétés renommées, avec OpenRewrite si le projet l'accepte. À utiliser pour toute montée de version de Spring Boot ou de Java dans un projet Spring.
---

# Montée de version Spring Boot

La méthode générale (filet de tests, étapes courtes, une version majeure à la fois) est dans l'agent `refactorer`. Ce skill donne l'ordre et les pièges propres à Spring Boot.

## Quand l'utiliser
- Montée de version mineure ou majeure de Spring Boot, ou de la version de Java d'un projet Spring.
- Une dépendance de sécurité impose une version plus récente de Spring Boot.

## Ce que l'agent rate sans ce skill
- Il saute directement de 2.x à 3.x (ou de 3.x à 4.x) sans passer par la dernière mineure de la génération actuelle, et perd les avertissements de dépréciation qui guidaient la migration.
- Il change la version du parent sans aligner les dépendances gérées à part (Spring Cloud, librairies tierces), et le projet compile avec des versions incompatibles.
- Il oublie les propriétés renommées : l'application démarre mais ignore silencieusement sa configuration.
- Il remplace `javax` par `jakarta` partout, y compris pour des paquets du JDK qui restent en `javax` (`javax.sql`, `javax.crypto`).

## Entrées
- Version actuelle et cible de Spring Boot et de Java, dépendances (`dependency:tree`), configuration, tests.

## Procédure
1. **Préparer** : suite de tests verte et commande citée ; branche dédiée ; liste des dépendances qui ont leur propre cycle de versions (Spring Cloud, Spring Modulith, librairies tierces liées à Spring).
2. **Lire** les notes de version et le guide de migration officiel de chaque version mineure entre l'actuelle et la cible (wiki Spring Boot « Spring Boot X.Y Release Notes » et « Migration Guide »), plus ceux de Spring Framework, Spring Security et Hibernate concernés. Liste les points qui touchent le projet.
3. **Passer à la dernière mineure de la génération actuelle** (par exemple 2.7.x avant 3.0, 3.5.x avant 4.0), corriger tous les avertissements de dépréciation, tests verts, commit.
4. **Ajouter temporairement `spring-boot-properties-migrator`** (dépendance d'exécution) : au démarrage, il signale et adapte les propriétés renommées ou retirées. Corrige la configuration, puis retire la dépendance dans la même PR.
5. **Monter Java d'abord si la cible l'exige** (Java 17 pour Spring Boot 3 et 4), en vérifiant les outils de build, l'image Docker et la CI.
6. **Changer la version de Spring Boot** et aligner les dépendances liées (BOM Spring Cloud compatible, versions des librairies tierces). OpenRewrite (recettes `org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_x` et suivantes) peut faire les changements mécaniques : lance-le seulement si le projet accepte l'outil, relis tout son diff, et ne le laisse pas dans le build final si personne ne l'utilise.
7. **Points connus par génération** :
   - **2 vers 3** : `javax.*` → `jakarta.*` pour Java EE seulement (persistence, validation, servlet, annotation, transaction) ; Spring Security 6 (`SecurityFilterChain`, `requestMatchers`, `@EnableMethodSecurity`, suppression de `WebSecurityConfigurerAdapter`) ; Hibernate 6 (types, séquences, requêtes) ; correspondance des URL sans barre finale par défaut ; propriétés `spring.redis.*` → `spring.data.redis.*`.
   - **3 vers 4** : Spring Framework 7, Jackson 3 (paquets `tools.jackson`, sauf annotations), starters réorganisés, JUnit à jour, API dépréciées en 3.x retirées (dont `@MockBean`) : suis le guide de migration de la version cible.
8. **Vérifier** à chaque étape : compilation sans avertissement de dépréciation nouveau, `./mvnw verify` ou `./gradlew check`, démarrage de l'application, parcours principaux (skill `e2e-testing` si le projet en a).
9. **Consigner** dans le journal et un ADR : versions de départ et d'arrivée, étapes, changements de comportement, dépendances alignées.

## Livrable
Le projet sur la version cible, tests verts, une entrée de journal et un ADR qui listent les étapes et les changements de comportement, la ligne de CHANGELOG si le comportement visible change.

## Vérifications
- Version effective vérifiée (`dependency:tree`) pour Spring Boot, Spring Framework, Spring Security et Hibernate.
- Plus aucune trace de `spring-boot-properties-migrator` ni d'avertissement de propriété renommée au démarrage.
- Suite complète verte, résumé cité.

## Limites
- Une montée de version qui oblige à changer d'image de production, de version de base de données ou d'infrastructure prépare le changement ; le déploiement reste une action réservée (règle 5 des principes communs).

## En cas de blocage
- Dépendance tierce sans version compatible : garder la version actuelle, consigner le blocage avec le ticket de la librairie, proposer une alternative selon la règle 4 des principes communs.
- Changement de comportement non couvert par les tests : ajouter le test d'abord (`test-engineer`), puis continuer.
