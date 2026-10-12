---
name: debugging-method
description: Méthode pour trouver la cause racine d'un bug avant de le corriger - reproduction fiable, lecture de l'erreur, réduction du cas, recherche du commit fautif avec git bisect, hypothèses prouvées une par une, tests instables, correctif minimal et recherche des jumeaux. À utiliser pour tout bug, régression, test rouge ou intermittent, erreur en production, et quand un premier correctif n'a pas suffi.
---

# Méthode de débogage

L'agent `debugger` définit les étapes (reproduire, isoler, prouver, corriger, verrouiller). Ce skill donne les techniques de chaque étape et les pièges qui font corriger le symptôme au lieu de la cause.

## Quand l'utiliser
- `debugger` : tout bug, régression ou incident.
- Tout agent dont un test devient rouge sans raison évidente, ou dont un premier correctif n'a pas suffi.
- `quality-gatekeeper` et `test-engineer` face à un test intermittent.

## Ce que l'agent rate sans ce skill
- Il corrige à l'endroit où l'erreur apparaît (ajout d'un `null` check, d'un `try/catch`, d'une valeur par défaut) au lieu de l'endroit où la donnée devient fausse.
- Il change plusieurs choses à la fois, puis ne sait pas laquelle a fait passer le test.
- Il lit la dernière ligne de la trace et rate la première exception (« Caused by », « Previous exception »), qui porte la cause.
- Il déclare un test « flaky » sans chercher pourquoi : ordre, horloge, données partagées, concurrence.
- Son correctif casse un cas voisin du même code, par exemple une entrée mal formée qui renvoyait 404 et renvoie maintenant 500.
- Il ne cherche pas le même défaut ailleurs, alors que le bug vient presque toujours d'un pattern recopié.
- Il débogue un état périmé : cache de configuration ou de routes, build ancien, mauvaise variable d'environnement, dépendance pas réinstallée.

## Entrées
- Le symptôme : comportement observé, attendu, étapes, environnement, message d'erreur complet, logs.
- Le dépôt, son historique git, la suite de tests.

## Procédure
1. **Fixer le symptôme par écrit** en une phrase vérifiable : « `GET /notes/12` par l'utilisateur 3 renvoie la note de l'utilisateur 5 avec un 200 ; attendu : 404 ». Sans phrase vérifiable, il n'y a pas de test possible.
2. **Lire l'erreur entièrement** :
   - la trace jusqu'à la première exception, dont le message et le premier cadre appartiennent au code du projet ;
   - les journaux juste avant l'erreur ;
   - la version exacte du langage, du framework et de la dépendance en cause (`composer show <paquet>`, `npm ls <paquet>`, `./gradlew dependencies`).
3. **Écarter l'état périmé** avant toute hypothèse : vider les caches du framework (`php artisan optimize:clear`, `bin/console cache:clear`, dossiers `.next/` ou `.angular/cache/`), réinstaller les dépendances depuis le fichier de verrouillage, vérifier quelles variables d'environnement sont réellement chargées.
4. **Reproduire par un test automatisé** au niveau le plus bas qui montre le bug (skill `testing-strategy`). Le test doit échouer pour la bonne raison : le message d'échec décrit le symptôme, pas une erreur de mise en place du test.
5. **Réduire le cas** : retire les données, étapes et paramètres un à un tant que le test reste rouge. Le cas minimal désigne souvent la cause directement.
6. **Situer la régression dans l'historique**, si le comportement marchait avant :
   ```bash
   git stash                                   # arbre de travail propre
   git bisect start <commit-mauvais> <commit-bon>
   git bisect run <commande qui sort en échec si le bug est présent>
   git bisect reset && git stash pop
   ```
   Le commit trouvé dit ce qui a changé ; le diff de ce commit est le premier suspect.
7. **Tenir un journal d'hypothèses** : une hypothèse à la fois, avec l'observation qui la confirmerait ou l'infirmerait. Observer avant de modifier : valeur intermédiaire journalisée, point d'arrêt, requête SQL réellement exécutée, réponse HTTP brute. Une hypothèse infirmée est rayée, jamais « corrigée quand même ».
8. **Remonter à l'origine de la donnée fausse** : la cause est l'endroit où la valeur devient incorrecte (requête sans filtre, conversion de type, fuseau horaire, état partagé), pas celui où elle provoque l'erreur.
9. **Corriger à l'origine, un seul changement**, puis relancer le test de reproduction. S'il ne passe pas, annule le changement avant d'en essayer un autre.
10. **Vérifier les voisins du correctif** : entrées mal formées, absentes, d'un autre utilisateur, limites. Ajoute un test pour chaque voisin que le correctif touche, notamment le code HTTP renvoyé pour une entrée invalide.
11. **Chercher les jumeaux** : recherche le même pattern dans tout le dépôt (`rg` sur l'appel ou la construction fautive). Corrige ceux de la même cause dans le même changement ; les autres deviennent des tâches du plan.
12. **Nettoyer** : retire journaux de diagnostic, points d'arrêt et code temporaire ; le test de reproduction reste dans la suite.

### Test intermittent
1. Le faire échouer à coup sûr :
   - le relancer en boucle : `for i in $(seq 20); do <commande> || { echo "échec au passage $i"; break; }; done`, ou `npx playwright test --repeat-each=20` ;
   - en ordre aléatoire avec une graine rejouable : `--order-by=random` puis `--random-order-seed=<graine>` (PHPUnit), `--randomize --seed=<graine>` (Jest).
2. Chercher, dans cet ordre :
   - données partagées entre tests, ou absence de remise à zéro ;
   - dépendance à l'heure, au fuseau horaire ou à la date du jour ;
   - ordre non garanti : requête sans `ORDER BY`, itération sur un ensemble non ordonné ;
   - attente fixe ou course entre deux opérations asynchrones ;
   - appel réseau réel.
3. Corriger la cause : horloge figée, tri explicite, attente d'une condition. N'ajoute jamais de `sleep` ni de nouvelle tentative automatique. Un test intermittent reste un échec (skill `quality-gates`).

## Livrable
Dans le compte rendu :
```markdown
**Symptôme** : <phrase vérifiable>
**Reproduction** : `tests/...::test_...` rouge avant, vert après
**Cause** : <où la donnée devient fausse, fichier:ligne> — preuve : <observation>
**Hypothèses écartées** : <hypothèse> — infirmée par <observation>
**Correctif** : <changement minimal> ; voisins testés : <cas>
**Jumeaux** : <corrigés> / <ajoutés au plan>
```

## Vérifications
- Le test de reproduction a été vu rouge avant le correctif, avec la commande et la sortie citées.
- La cause citée s'appuie sur une observation, pas sur une lecture du code seule.
- La recherche des jumeaux est citée avec sa commande.
- Suite complète verte ; aucun code de diagnostic dans le diff.

## Limites
- Ce skill ne couvre pas la limitation d'impact d'un incident en production, qui est une action réservée (règle 5 des principes communs, mode incident de `debugger`).
- Un problème de lenteur relève du skill `profiling` ; ce skill s'arrête quand le comportement est correct mais lent.

## En cas de blocage
- Pas de reproduction après logs, historique, données de test et variations d'environnement : livre le journal d'hypothèses classées par probabilité, et ce qu'il faudrait observer (journal à ajouter, donnée à capturer) pour trancher.
- Cause hors du dépôt (dépendance, service externe) : prouve-le avec un cas minimal, contourne au plus près de la frontière avec un commentaire qui cite le défaut amont, et ajoute la mise à jour à surveiller au plan.
- Correctif qui exige un changement de conception : livre le test rouge et la cause prouvée, et escalade à `architect`.
