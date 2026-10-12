---
name: task-breakdown
description: Découper une fonctionnalité ou un projet en tâches petites, ordonnées par dépendances, chacune vérifiable isolément et réalisable par un agent en une session. À utiliser pour écrire ou réviser docs/plan.md, ou pour découper une demande trop large avant de l'implémenter.
---

# Découpage en tâches

## Quand l'utiliser
- `planner` : produire `docs/plan.md` à partir de la spec et de l'architecture.
- `orchestrator` ou un agent d'implémentation : une demande est trop large pour être faite et vérifiée d'un coup.

## Ce que l'agent rate sans ce skill
- Des tâches trop grosses (« faire l'authentification »), impossibles à vérifier et à relire.
- Des tâches découpées par fichier ou par couche technique pure, qui laissent le projet cassé entre deux tâches.
- Des dépendances implicites : une tâche qui suppose une table ou un composant créé « plus tard ».
- Des tâches sans critère de fin, donc jamais vraiment terminées.

## Entrées
- `docs/spec.md` (stories, critères, règles), `docs/architecture.md`, le code existant de la zone.

## Procédure
1. **Partir des stories Must** et de leurs critères ; les Should et Could viennent après, en tâches séparées.
2. **Découper en tranches verticales minces** quand c'est possible : une tâche livre un comportement observable de bout en bout (donnée → logique → API ou écran → test), même réduit. Découper par couche seulement quand une base commune est nécessaire avant tout le reste (schéma, design system, client d'API).
3. **Taille d'une tâche** : un diff relisable en une fois (repère : une quinzaine de fichiers et quelques centaines de lignes au plus), un critère « terminé » prouvable par un test ou une commande, et un projet qui compile et dont les tests passent à la fin.
4. **Lever l'incertitude d'abord** : une tâche d'exploration (spike) courte et bornée pour toute inconnue technique (API externe, performance, librairie), avec un livrable de décision, pas de code de production.
5. **Ordonner par dépendances** : données et contrats → logique métier → API ou contrôleurs → interface → parcours de bout en bout → documentation. Les tâches indépendantes peuvent être marquées parallélisables.
6. **Remplir chaque tâche** :

```markdown
### T4 · Limiter les tentatives de connexion
- Story / règles : US-03, RG-02
- Zone : app/Http/Controllers/Auth, routes/web.php
- Réutiliser : RateLimiter natif, LoginRequest existant
- Dépend de : T2
- Agent : laravel-implementer
- Risque de régression : faible (routes login uniquement)
- Terminé quand : 6e tentative en moins d'une minute → 429, prouvé par tests/Feature/LoginThrottleTest.php
- Statut : à faire
```

7. **Vérifier la couverture** : chaque critère Must de la spec est couvert par au moins une tâche ; aucune tâche ne fait quelque chose que la spec ne demande pas (sinon elle sort du plan ou devient une hypothèse consignée).

## Livrable
`docs/plan.md` : liste ordonnée des tâches au format ci-dessus, avec en tête un tableau récapitulatif (identifiant, titre, dépendances, statut) la liste des hypothèses retenues et, s'il y en a, des décisions humaines requises (actions réservées uniquement).

## Vérifications
- Chaque tâche a un critère « terminé » vérifiable et un agent recommandé.
- Le graphe des dépendances n'a pas de cycle ; aucune tâche ne dépend d'une tâche placée après elle.
- Tous les critères Must sont couverts.

## Limites
- Le plan ne remet pas en cause l'architecture : un problème de conception est signalé à `architect`.
- Pas d'estimation en jours : la taille se juge au périmètre et au diff.

## En cas de blocage
- Spec trop floue pour découper : renvoie les points flous à `product-analyst`, qui les tranche en hypothèses ; sans lui, tranche selon le skill `autonomy-policy` et consigne.
