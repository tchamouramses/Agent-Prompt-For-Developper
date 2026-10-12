---
name: refactoring-patterns
description: Restructurer du code à comportement strictement identique - tests de caractérisation avant de toucher, odeurs de code reliées au refactoring qui les traite (extraire, déplacer, renommer, remplacer une condition par du polymorphisme, introduire un objet paramètre), changement en parallèle pour les signatures publiques, détection sûre du code mort y compris les usages dynamiques propres à chaque framework, une transformation par étape vérifiée et committée, mesure du gain. À utiliser pour supprimer duplication et code mort, simplifier une fonction ou une classe, réorganiser des modules, et préparer un changement fonctionnel difficile.
---

# Patterns de refactoring

Les principes des agents qui modifient du code fixent l'objectif (lisibilité, pas de répétition, SOLID sans abstraction inutile, zéro code mort) ; `refactorer` fixe la démarche (filet, plan, petites étapes). Ce skill donne les transformations et leurs pièges. Les montées de version relèvent des skills `upgrade-*` du framework.

## Quand l'utiliser
- `refactorer` : toute restructuration.
- Agents d'implémentation : refactoring préparatoire dans le périmètre de la tâche (« rendre le changement facile, puis faire le changement facile »), dans un commit séparé.
- `code-reviewer` : pour nommer précisément la transformation à demander.

## Ce que l'agent rate sans ce skill
- Il refait toute la zone d'un coup : quarante fichiers modifiés, tests rouges, impossible de savoir quelle étape a cassé.
- Il change le comportement sans le voir : ordre d'une liste, type d'exception levée, traitement de `null` ou de la chaîne vide, arrondi, requêtes SQL en plus, message d'erreur affiché.
- Il « corrige » au passage un comportement étrange dont quelqu'un dépend.
- Il fusionne deux blocs qui se ressemblent mais changent pour des raisons différentes, puis ajoute des paramètres booléens pour les distinguer : la mauvaise abstraction coûte plus que la duplication.
- Il supprime comme « mort » du code appelé dynamiquement (route déclarée par chaîne, écouteur découvert automatiquement, fichier de route Next.js ou Expo Router, bean Spring, méthode appelée depuis un template).
- Il renomme un champ sérialisé, une colonne ou une route publique en le croyant interne.
- Il mélange reformatage et refactoring : le diff devient illisible pour la revue.

## Entrées
- La zone, l'objectif mesurable (« supprimer les trois copies du calcul de TVA »), les tests qui la couvrent et leur état, les consommateurs hors du module (skill `change-impact-analysis`).

## Procédure
1. **Poser le filet** : lance les tests de la zone. Si un comportement n'est pas couvert, écris des tests de caractérisation qui figent la sortie actuelle, même étrange (entrées limites, erreurs, ordre), avant toute transformation. Un comportement étrange reste tel quel et est signalé à `debugger`.
2. **Relier chaque odeur à sa transformation** :

| Odeur | Transformation |
|-------|----------------|
| fonction longue, commentaire qui annonce un bloc | extraire une fonction nommée d'après le commentaire |
| même logique en trois endroits, ou en deux si règle métier | extraire puis remplacer chaque copie, une à la fois |
| `switch` ou chaîne de `if` sur un type, répétée | remplacer la condition par du polymorphisme (une implémentation par variante) |
| liste de paramètres longue, mêmes trios passés partout | introduire un objet paramètre ou un objet valeur |
| méthode qui utilise surtout les données d'une autre classe | déplacer la méthode |
| classe qui change pour plusieurs raisons | extraire une classe par responsabilité |
| conditions imbriquées | retours anticipés, clauses de garde |
| abstraction avec un seul usage, couche qui ne fait que déléguer | réintégrer (inline) |
| nom trompeur | renommer, avec recherche de toutes les occurrences, chaînes comprises |

3. **Vérifier qu'une ressemblance est une vraie duplication** : les deux copies changent-elles pour la même règle ? Si non, garde-les séparées.
4. **Écrire le plan** dans le journal : étapes courtes, chacune laissant le code compilable et les tests verts.
5. **Une transformation par étape** : appliquer, lancer les tests de la zone et l'analyse statique, committer (`refactor: extraire le calcul de TVA`). Rouge : `git restore` de l'étape, puis une étape plus petite ; jamais de correctifs empilés.
6. **Signature publique ou contrat** (méthode appelée hors du module, route, champ sérialisé, événement) : changement en parallèle. Ajoute la nouvelle forme, fais migrer les appelants un par un, puis retire l'ancienne quand la recherche ne trouve plus d'usage ; si un usage est hors du dépôt, garde l'ancienne forme dépréciée et ajoute sa suppression au plan (skill `api-contracts`).
7. **Prouver le code mort avant de supprimer** :
   - recherche du nom dans tout le dépôt, chaînes, configurations et templates compris (`rg -n "<nom>"`) ;
   - analyse statique : `vendor/bin/phpstan analyse` (PHP), `npx tsc --noEmit` et `knip` s'il est présent (TypeScript), avertissements du compilateur et de l'IDE (Java) ;
   - usages dynamiques : `php artisan route:list` et `php artisan event:list` (Laravel), `php bin/console debug:container` et `debug:router` (Symfony), composants annotés et `@Bean` (Spring Boot), fichiers `app/**/page.tsx` et `route.ts` (Next.js), dossier `app/` d'Expo Router, sélecteurs et templates (Angular).
8. **Mesurer** à la fin : lignes supprimées, copies retirées, complexité de la fonction principale avant et après si l'outil du projet la donne.

## Livrable
```markdown
**Objectif** : <mesurable>
**Filet** : <tests existants> + <tests de caractérisation ajoutés>
**Étapes** : 1. <transformation> — commit <sha court> — tests verts …
**Résultat** : −<n> lignes, <n> copies supprimées, <symboles> supprimés (preuve : recherche citée)
**Comportement conservé volontairement** : <bizarrerie> — test <nom>, signalé à `debugger`
**Transitions** : <ancienne signature dépréciée> — suppression en tâche <Tx>
```

## Vérifications
- Aucun test existant modifié dans son attendu ; seuls des tests ont été ajoutés.
- Tests, lint, analyse statique et build verts à la fin, commandes citées.
- Chaque suppression de code mort cite sa preuve de non-usage, usages dynamiques compris.
- Le diff ne contient ni reformatage hors zone ni changement fonctionnel.

## Limites
- Ce skill ne couvre pas les montées de version de framework (skills `upgrade-*`) ni un changement d'architecture (`architect`).
- Les outils de transformation automatique (Rector, OpenRewrite, codemods) ne s'utilisent que s'ils sont déjà dans le projet ou choisis selon la règle 4 des principes communs ; leur diff se relit comme un diff manuel.

## En cas de blocage
- Zone impossible à tester sans la modifier : premier changement minimal pour créer un point d'injection (paramètre, interface à la frontière), vérifié par lecture et par la suite existante, puis tests, puis refactoring.
- Étape qui reste rouge après deux découpages : arrête-toi au dernier état vert, livre ce qui est fait et décris l'obstacle dans le compte rendu.
