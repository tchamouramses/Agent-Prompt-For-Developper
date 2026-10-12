---
name: lint-format-java
description: Mettre en place et utiliser le formatage et l'analyse statique Java (Spotless avec google-java-format ou Palantir, Checkstyle, PMD, SpotBugs, Error Prone) avec Maven ou Gradle - choisir les outils d'un nouveau projet, les brancher sur la CI, corriger sans faire taire les règles. À utiliser à l'initialisation d'un projet Java ou quand un contrôle de style ou d'analyse échoue.
---

# Formatage et analyse statique Java

## Quand l'utiliser
- `scaffolder` : initialiser un projet Java ou Spring Boot.
- Tout agent : un contrôle de formatage ou d'analyse échoue, ou il faut savoir quelle commande lancer.

## Ce que l'agent rate sans ce skill
- Il reformate tout un fichier ou tout le projet dans une tâche sans rapport, et le diff devient illisible.
- Il ajoute un deuxième formateur qui se bat avec celui du projet.
- Il fait passer l'analyse en ajoutant des exclusions ou en baissant le seuil au lieu de corriger.
- Il lance l'outil à la main avec une configuration différente de celle de la CI.

## Entrées
- `pom.xml` ou `build.gradle(.kts)` (plugins `spotless`, `checkstyle`, `pmd`, `spotbugs`, `errorprone`), fichiers de règles (`checkstyle.xml`, `pmd-ruleset.xml`, `spotbugs-exclude.xml`), `.editorconfig`, workflows de CI.

## Procédure

### 1. Projet existant : utiliser ce qui est là
| Outil | Vérifier | Corriger |
|-------|----------|----------|
| Spotless (Maven) | `./mvnw spotless:check` | `./mvnw spotless:apply` |
| Spotless (Gradle) | `./gradlew spotlessCheck` | `./gradlew spotlessApply` |
| Checkstyle | `./mvnw checkstyle:check` ou `./gradlew checkstyleMain` | à la main |
| PMD | `./mvnw pmd:check` ou `./gradlew pmdMain` | à la main |
| SpotBugs | `./mvnw spotbugs:check` ou `./gradlew spotbugsMain` | à la main |
| Error Prone | à la compilation | à la main |

- Lance les commandes de la CI (skill `repository-discovery`) ; `./mvnw verify` ou `./gradlew check` les exécutent souvent toutes.
- Spotless avec `ratchetFrom` ne vérifie que les fichiers modifiés depuis une branche : garde ce réglage s'il existe. Sans lui, n'applique le formateur qu'aux fichiers de ta tâche (cible `-DspotlessFiles=<regex>` en Maven) et vérifie que `git diff` ne touche pas d'autres fichiers.

### 2. Nouveau projet : socle par défaut
Choisis selon le skill `autonomy-policy` et consigne le choix ; par défaut :
- **Formatage** : Spotless avec google-java-format (ou Palantir Java Format, plus lisible à 120 colonnes), `removeUnusedImports`, fin de ligne et encodage fixés ; `ratchetFrom 'origin/main'` si le projet existe déjà.
- **Analyse** : Error Prone à la compilation, ou SpotBugs ; Checkstyle seulement pour des règles que le formateur ne couvre pas (nommage, imports interdits). Un seul outil par famille de règles.
- **Seuils** : l'analyse échoue sur toute nouvelle erreur ; les erreurs existantes vont dans un fichier d'exclusion daté, jamais les nouvelles.
- **CI** : le contrôle de formatage et l'analyse tournent dans la même commande que les tests (`verify` ou `check`).
- **Éditeur** : `.editorconfig` cohérent avec le formateur.

### 3. Corriger un échec
1. Lis la règle et la ligne citées ; corrige le code.
2. Formatage : lance la commande de correction, puis relis le diff produit.
3. Faux positif avéré : suppression locale et ciblée (`@SuppressWarnings("NomDeRegle")` ou `// NOPMD - raison`) avec la raison, jamais une exclusion globale ; cite-la dans le compte rendu.

## Livrable
Pour un nouveau projet : la configuration des outils, branchée sur la CI, et sa justification dans le journal. Pour une tâche : les commandes lancées et leur résultat.

## Vérifications
- La commande de vérification de la CI passe en local.
- `git diff --stat` ne contient pas de fichiers reformatés hors de la tâche.
- Aucun seuil abaissé ni exclusion globale ajoutée.

## Limites
- Les règles de style du code (nommage, immuabilité, exceptions) sont dans le skill `coding-conventions-java` ; ce skill porte les outils.

## En cas de blocage
- L'outil du projet ne se lance pas (version de Java incompatible avec le plugin) : signale la version requise, lance ce qui fonctionne et marque le reste **non vérifié**.
- Le projet n'a aucun outil : n'en ajoute pas dans une tâche sans rapport ; propose le socle de l'étape 2 comme tâche du plan.
