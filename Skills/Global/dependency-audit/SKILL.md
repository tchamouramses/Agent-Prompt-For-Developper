---
name: dependency-audit
description: Auditer les dépendances d'un projet sans le modifier - vulnérabilités connues (composer audit, npm audit, OWASP Dependency-Check pour Maven et Gradle), paquets abandonnés ou obsolètes, licences incompatibles, puis classement par exploitabilité réelle et plan de mise à jour découpé confié à l'agent qui modifie le code. À utiliser pour tout audit de sécurité, avant une version, à l'ajout d'une dépendance et quand la CI signale une vulnérabilité.
---

# Audit des dépendances

Les critères d'une dépendance acceptable (licence permissive, maintenue, sans vulnérabilité connue) sont dans la règle 4 des principes communs et le skill `autonomy-policy` ; une licence copyleft forte ou commerciale revient à l'humain. `security-auditor` n'a pas d'outil d'écriture : il audite et propose, la mise à jour est faite par `refactorer`. Ce skill donne la méthode.

## Quand l'utiliser
- `security-auditor` : étape « Dépendances » de l'audit.
- Avant la préparation d'une version, et quand la CI ou une alerte du dépôt signale une vulnérabilité.
- Tout agent qui ajoute une dépendance, pour vérifier les critères de la règle 4.

## Ce que l'agent rate sans ce skill
- Il lance `npm audit fix --force`, `composer update` ou une montée de version pendant l'audit : le dépôt change, des versions majeures arrivent sans test. Un audit ne modifie rien.
- Il audite sans fichier de verrouillage, ou un fichier non à jour : les versions analysées ne sont pas celles installées.
- Il recopie la sortie brute : 40 alertes dont 35 en dépendances de développement, sans dire lesquelles sont atteignables en production.
- Il propose de monter chaque dépendance transitive à la main au lieu de la dépendance directe ou de la BOM qui la tire (Spring Boot).
- Il ignore une alerte sans justification ni date de réexamen, et elle reste ignorée pour toujours.
- Il oublie les paquets abandonnés et les licences, que les outils de vulnérabilités ne signalent pas tous.
- Il regroupe une montée de version majeure avec des correctifs mineurs : une régression devient impossible à isoler.

## Entrées
- Les manifestes et fichiers de verrouillage (`composer.json` et `composer.lock`, `package.json` et `package-lock.json`, `pnpm-lock.yaml` ou `yarn.lock`, `pom.xml`, `build.gradle(.kts)`), les versions du langage et du framework, les exceptions déjà consignées (`docs/securite/`).

## Procédure
1. **Vérifier le verrouillage** : fichier de verrouillage présent et versionné (`git ls-files composer.lock package-lock.json`), cohérent avec le manifeste (`composer validate`, `npm ls --all` sans erreur). Sans fichier de verrouillage, c'est un constat en soi.
2. **Lancer l'audit de l'écosystème**, sortie JSON gardée dans `/tmp` :

| Écosystème | Vulnérabilités | Obsolètes | Licences |
|------------|----------------|-----------|----------|
| Composer (Laravel, Symfony) | `composer audit --format=json` (signale aussi les paquets abandonnés) | `composer outdated --direct` | `composer licenses --format=json` |
| npm (Angular, Next.js, Expo) | `npm audit --json`, puis `npm audit --omit=dev` pour la production | `npm outdated` | champ `license` de `package-lock.json` : `jq -r '.packages \| to_entries[] \| "\(.key) \(.value.license // "inconnue")"' package-lock.json` |
| pnpm / Yarn | `pnpm audit --json` / `yarn npm audit` (Yarn 2+) ou `yarn audit` (Yarn 1) | `pnpm outdated` / `yarn outdated` | outil déjà présent dans le projet |
| Maven (Spring Boot) | `mvn org.owasp:dependency-check-maven:check` (rapport dans `target/`) | `mvn versions:display-dependency-updates` | `mvn org.codehaus.mojo:license-maven-plugin:aggregate-add-third-party` |
| Gradle (Spring Boot) | `./gradlew dependencyCheckAnalyze` si le plugin OWASP est déclaré | `./gradlew dependencyUpdates` si le plugin est déclaré | `./gradlew dependencies` puis licences des directes |

   Compléments de framework, en lecture seule : `npx expo install --check` (versions attendues par le SDK Expo), `ng update` sans argument (mises à jour Angular disponibles).
3. **Qualifier chaque alerte** : identifiant (CVE, GHSA), paquet et version, directe ou transitive (`composer why <paquet>`, `npm explain <paquet>`, `mvn dependency:tree -Dincludes=<groupe>:<artefact>`), production ou développement, correctif disponible, code vulnérable atteint ou non (recherche de l'API concernée dans le dépôt).
4. **Classer** : gravité de l'avis ajustée par l'exploitabilité. Une faille critique dans un outil de build absent de l'image de production descend ; une faille moyenne sur un parseur exposé aux entrées utilisateur monte. Barème du skill `owasp-checklist`.
5. **Licences** : permissives acceptées (MIT, Apache-2.0, BSD, ISC ; MPL-2.0 sans modification) ; GPL, AGPL, LGPL selon la liaison, SSPL, licence commerciale ou absente → décision humaine préparée (règle 4).
6. **Maintenance** : paquet abandonné, sans version depuis plus de 12 mois ou à dépôt archivé → remplacement proposé avec 2 ou 3 candidats évalués selon le skill `autonomy-policy`.
7. **Plan de mise à jour**, une tâche par lot :
   - correctifs et versions mineures d'une même famille, groupés, avec la suite de tests ;
   - chaque version majeure seule, avec son guide de migration (skill `version-compatibility`) ;
   - transitive : montée de la dépendance directe qui la tire, sinon contrainte ciblée (`overrides` npm, propriété de version de la BOM Spring Boot, contrainte Composer) commentée et à retirer plus tard.
8. **Exceptions** : une alerte acceptée (pas de correctif, code non atteint) est consignée avec la raison, la date de réexamen et l'avis concerné, et jamais par un ignore global.

## Livrable
Section « Dépendances » du rapport de `security-auditor` :
```markdown
## Dépendances (<outil et version>, <date>)
| Avis | Paquet (version) | Directe / transitive | Prod / dev | Atteint | Gravité retenue | Correctif |
|------|------------------|----------------------|------------|---------|-----------------|-----------|
| GHSA-xxxx | vendor/paquet (1.2.3) | transitive via vendor/autre | prod | oui (`fichier:ligne`) | haute | 1.2.5 |
**Abandonnés** : <paquet → remplaçant proposé>
**Licences à décider** : <paquet, licence, usage>
**Plan** : T-a correctifs groupés (`refactorer`) ; T-b montée majeure <paquet> (`refactorer`)
**Exceptions** : <avis, raison, réexamen le AAAA-MM-JJ>
```

## Vérifications
- Commandes citées avec leur version et le décompte par gravité (skill `evidence-tracking`).
- `git status --porcelain` vide après l'audit : aucun manifeste ni fichier de verrouillage modifié.
- Chaque alerte haute ou critique a une qualification complète (étape 3).

## Limites
- OWASP Dependency-Check télécharge la base NVD : premier passage long, et une clé d'API NVD est un compte tiers, donc une décision humaine. Sans réseau ni base, marque l'audit Java **non vérifié**.
- Les bases d'avis ne couvrent que les failles publiées : un audit vert n'est pas une garantie.

## En cas de blocage
- Outil absent ou hors ligne : audit partiel sur les écosystèmes disponibles, le reste marqué **non vérifié** avec la commande à lancer.
- Correctif inexistant pour une faille atteinte : propose une mitigation dans le code (validation en entrée, fonction évitée) ou un remplaçant, et classe la faille dans « Dette technique et risques ».
