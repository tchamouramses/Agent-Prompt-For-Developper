---
name: testing-strategy
description: Choisir quels tests écrire, à quel niveau (unitaire, intégration, contrat, bout en bout) et sur quels cas, selon le risque et le comportement à protéger ; rendre les tests fiables. À utiliser avant d'écrire des tests, pour définir la stratégie d'un projet ou d'une fonctionnalité, et pour juger si une couverture suffit.
---

# Stratégie de test

## Quand l'utiliser
- Avant d'écrire les tests d'une tâche (agents d'implémentation, `debugger`, `refactorer`).
- `test-engineer` : définir la stratégie d'une fonctionnalité ou du projet, combler les manques.
- `code-reviewer`, `quality-gatekeeper` : juger si les tests protègent vraiment le comportement.

## Ce que l'agent rate sans ce skill
- Des tests qui vérifient l'implémentation (appels de méthodes simulées) au lieu du comportement : ils cassent au moindre refactoring et ne détectent pas les bugs.
- Tout tester en unitaire avec des simulations, y compris la base de données, et rater les vrais bugs d'intégration (requête, transaction, sérialisation).
- Le seul cas nominal.
- Des tests fragiles : dépendance à l'heure, à l'ordre d'exécution, à des données partagées, à des `sleep`.
- Des tests modifiés pour passer au lieu de corriger le code.

## Entrées
- Les critères d'acceptation et règles métier (spec), la tâche, les tests existants et leurs conventions (skill `repository-discovery`).

## Procédure
1. **Partir du comportement à protéger** : chaque critère d'acceptation et chaque règle métier de la tâche doit être vérifié par au moins un test qui échouerait si le comportement disparaissait.
2. **Choisir le niveau le plus bas qui prouve le comportement réel** :

| Niveau | Pour | Exemples |
|--------|------|----------|
| Unitaire | logique pure : calculs, règles, transformations, validations | calcul d'une remise, machine à états |
| Intégration | code + infrastructure réelle de test : base, file, cache, système de fichiers | requête Eloquent ou JPA, transaction, migration, repository |
| Fonctionnel / API | une route ou un écran de bout en bout côté serveur, avec authentification et autorisations | test Feature Laravel, `WebTestCase` Symfony, `MockMvc` / `@SpringBootTest`, test de route Next.js |
| Contrat | format échangé entre deux parties | schéma de réponse d'API, payload de webhook (skill `api-contracts`) |
| Bout en bout | quelques parcours critiques dans l'application lancée | inscription, paiement (agent `e2e-validator`) |

   Beaucoup de tests unitaires et d'intégration, des tests fonctionnels pour chaque route ou écran touché, peu de bout en bout.
3. **Ne simuler que les frontières** : services externes (paiement, e-mail, API tierces), horloge, aléatoire. Pas de simulation de la base de données ni du code du projet quand un test d'intégration est possible.
4. **Couvrir les familles de cas** du skill `acceptance-criteria` qui s'appliquent : erreurs de saisie, droits (non connecté, rôle insuffisant, ressource d'autrui), vide et limites, doublons, échec d'un service externe, transitions d'état interdites.
5. **Pour un bug** : écrire d'abord le test qui reproduit le bug et le voir échouer, puis corriger.
6. **Rendre les tests fiables** :
   - données créées par le test lui-même (factories), isolées (transaction annulée ou base réinitialisée), sans dépendance à l'ordre ;
   - horloge et aléatoire figés ;
   - attentes explicites sur une condition, jamais de `sleep` ;
   - un test, un comportement ; un nom qui décrit le comportement et cite l'identifiant (`US-03.2`, `RG-04`).
7. **Ne jamais affaiblir un test pour le faire passer** (assertion retirée, test sauté, valeur attendue recopiée depuis le résultat) : si le test a raison, corrige le code ; s'il a tort, explique pourquoi dans le compte rendu.

## Livrable
Les tests, et dans le compte rendu une ligne par critère ou règle : identifiant → test(s) qui le couvrent.

## Vérifications
- Chaque nouveau test a été vu en échec au moins une fois quand c'est possible (bug reproduit, ou comportement retiré temporairement), puis en succès.
- La suite de la zone passe, avec la commande et le résultat cités.

## Limites
- Utilise les outils de test du projet ; un nouvel outil ne s'ajoute que si aucun n'existe pour ce niveau de test, selon la règle 4 des principes communs.
- La couverture en pourcentage n'est pas un objectif ; la couverture des critères l'est.

## En cas de blocage
- Comportement attendu ambigu : `product-analyst` tranche ; sans lui, retiens l'hypothèse la plus prudente, consigne-la et nomme le test d'après elle.
- Code impossible à tester sans restructuration : signale-le et propose le changement minimal (injection de la dépendance) au lieu de restructurer hors de ta tâche.
