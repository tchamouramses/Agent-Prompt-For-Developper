---
name: coding-conventions-java
description: Écrire du Java moderne cohérent avec le projet - fonctionnalités autorisées par la version de Java installée (records, sealed, pattern matching, threads virtuels), immuabilité, Optional et null, exceptions, journalisation, Lombok selon le projet. À utiliser pour écrire ou relire du code Java.
---

# Conventions Java

Les règles générales (lisibilité, SOLID, zéro code mort, changement minimal) sont dans les principes des agents qui modifient du code. Ce skill les traduit en Java.

## Quand l'utiliser
- Écrire, refactorer ou relire du code Java (Spring Boot ou autre).

## Ce que l'agent rate sans ce skill
- Il écrit une syntaxe absente de la version de Java du projet (`switch` avec motifs en 17, collections séquencées en 17), ou au contraire du Java 8 verbeux dans un projet en Java 21.
- Il utilise `Optional` comme champ ou paramètre, ou appelle `.get()` sans test.
- Il retourne `null` pour une collection vide, ou laisse fuir une liste mutable interne.
- Il attrape `Exception` pour continuer, ou enveloppe une exception sans sa cause.
- Il mélange Lombok et code écrit à la main contrairement au projet, ou met `@Data` sur une entité JPA.
- Il construit les messages de journal par concaténation et y met des données sensibles.

## Entrées
- Version de Java (`maven.compiler.release`, `java.version`, toolchain Gradle, `java -version`), configuration de style et d'analyse (`.editorconfig`, Spotless, Checkstyle, PMD, SpotBugs, Error Prone), présence de Lombok, fichiers voisins.

## Procédure
1. **Version de Java** : retiens la version de compilation du projet. Fonctionnalités par version LTS :

| Version | Disponible |
|---------|------------|
| 11 | `var` (10), `List.of()` et `Map.of()` (9), méthodes de `String` (`isBlank`, `strip`, `lines`) |
| 17 | records, classes `sealed`, `instanceof` avec motif, blocs de texte `"""`, expressions `switch` |
| 21 | `switch` avec motifs et gardes `when`, motifs de records, threads virtuels, `SequencedCollection` (`getFirst()`, `reversed()`) |
| 25 | motifs non nommés `_` (22), déclarations avant `super(...)` dans les constructeurs, `ScopedValue` |

2. **Modélisation** :
   - record pour un DTO, une valeur ou un résultat immuable ; validation dans le constructeur compact ;
   - `enum` pour un ensemble fermé, `sealed interface` + records pour une alternative de cas traitée par un `switch` exhaustif (sans `default`, le compilateur signale le cas oublié) ;
   - champs `private final`, collections exposées par `List.copyOf()` ou vues non modifiables ; jamais de `null` pour une collection, renvoyer une collection vide.
3. **Null et `Optional`** : `Optional` seulement comme type de retour d'une recherche ; jamais en champ, paramètre ou élément de collection. Consomme-le avec `orElseThrow()`, `map()`, `ifPresent()`, jamais `.get()` seul. Suis les annotations de nullité du projet (JSpecify, `@Nullable` de Spring) si elles existent.
4. **Exceptions** : exceptions non vérifiées et nommées pour les erreurs métier (`CommandeDejaPayeeException`), traduites en réponse HTTP à un seul endroit (gestionnaire global) ; en enveloppant, passer la cause (`new XException("…", e)`) ; `catch` seulement là où tu sais quoi faire ; jamais de bloc vide ni de `printStackTrace()`. Ressources fermées par `try-with-resources`.
5. **Flux et boucles** : streams pour transformer ou filtrer une collection lisiblement ; boucle classique dès que la logique a des effets de bord, des sorties anticipées ou plus de trois étapes. Pas de stream parallèle sans mesure.
6. **Lombok** : suis le projet. S'il l'utilise : `@RequiredArgsConstructor` pour l'injection, `@Getter` ciblé, jamais `@Data` ni `@EqualsAndHashCode` sur une entité JPA. S'il ne l'utilise pas, ne l'ajoute pas : un record couvre la plupart des besoins.
7. **Journalisation** : SLF4J avec paramètres (`log.info("Commande {} payée", id)`), jamais de concaténation ; niveau adapté (`debug` pour le détail, `warn` pour l'anormal récupéré, `error` avec l'exception en dernier argument) ; aucun mot de passe, jeton ni donnée personnelle inutile.
8. **Nommage** : classes en `PascalCase`, méthodes et variables en `camelCase`, constantes en `UPPER_SNAKE_CASE`, paquets en minuscules par fonctionnalité (`com.exemple.facturation`) ; noms de méthodes qui disent l'intention (`annulerCommande`, pas `process`).
9. **Style et analyse** : outils et commandes du skill `lint-format-java` ; applique le formateur du projet à tes fichiers seulement.

## Livrable
Du code conforme, et dans le compte rendu les commandes de formatage et d'analyse lancées avec leur résultat.

## Vérifications
- Compilation sans nouvel avertissement (`-Xlint` si le projet l'active) et aucune syntaxe au-dessus de la version de Java retenue.
- Formatage et analyse statique sans nouvelle erreur sur les fichiers touchés.
- Aucun `@SuppressWarnings` ou exclusion d'analyse ajouté sans justification écrite dans le compte rendu.

## Limites
- Les conventions déjà en place dans le projet l'emportent sur ce skill (principes communs, règle 1). Ce skill sert quand le projet ne tranche pas.
- Les règles propres à Spring : skill `spring-boot`.

## En cas de blocage
- Version de Java d'exécution inférieure à celle de compilation : signale l'écart, code pour la plus basse, et marque l'exécution **non vérifiée**.
- Outil d'analyse absent : n'en installe pas un dans une tâche sans rapport ; suis le style des fichiers voisins et propose l'outil dans le compte rendu.
