---
name: quality-gates
description: Règles bloquantes de livraison, preuves exigées par contrôle, contrôles à refaire après une correction, et gabarits de matrice de traçabilité et de rapport de livraison. À utiliser par quality-gatekeeper pour rendre un verdict, par l'orchestrateur pour choisir les contrôles d'un parcours, et par devops-engineer pour traduire les règles en CI bloquante.
---

# Portes de qualité

## Quand l'utiliser
- `quality-gatekeeper` : verdict de livraison.
- `orchestrator` : choix des contrôles selon le profil (léger ou livraison) et après un refus.
- `devops-engineer` : configuration de la CI pour qu'elle bloque sur les mêmes règles.

## Ce que l'agent rate sans ce skill
- Il accepte sur la foi des comptes rendus au lieu de ré-exécuter.
- Il assouplit une règle en cours de route (« un seul test rouge, c'est un flaky »).
- Après une correction, il ne refait que le contrôle qui avait échoué, alors que la correction a pu casser autre chose.
- Il produit un rapport illisible pour quelqu'un qui ne lit pas le code.

## Entrées
- `docs/spec.md`, `docs/plan.md`, les rapports des agents de contrôle, l'état de la CI, le livrable (branche ou commit).

## Procédure
1. **Construire la matrice de traçabilité** : chaque story, critère et règle du périmètre → tâches → tests → parcours e2e → preuve (skill `evidence-tracking`).
2. **Ré-exécuter les contrôles clés** sur le commit livré : suite complète de tests, lint, analyse statique ou typage, build. Comparer aux résultats déclarés ; tout écart est une anomalie.
3. **Appliquer les règles bloquantes** selon le profil :

| Règle | Léger | Livraison |
|-------|:-----:|:---------:|
| Tests, lint, typage ou build en échec sur le commit livré | bloquant | bloquant |
| Test supprimé, sauté ou affaibli par le changement | bloquant | bloquant |
| Point bloquant de `code-reviewer` ouvert | bloquant | bloquant |
| Dépendance ajoutée hors critères ou sans comparaison consignée | bloquant | bloquant |
| Projet multilingue : clé manquante, vide ou en trop dans une langue, ou texte visible en dur dans le diff (skill `i18n`) | bloquant | bloquant |
| Critère d'acceptation Must sans test ni preuve | bloquant | bloquant |
| Code mort introduit | important | bloquant |
| Parcours e2e critique non validé | — | bloquant |
| Faille critique ou haute ouverte (`security-auditor`) | — | bloquant |
| Migration sans retour arrière testé ou plan de correction | — | bloquant |
| Objectif de performance défini et non atteint | — | bloquant |
| Écart bloquant avec le design (skill `design-fidelity-review`) | — | bloquant |

   Un échec « intermittent » reste un échec : il est relancé une fois ; s'il échoue encore, il bloque.
   Les règles portent sur le changement livré : un défaut préexistant dans du code que le changement ne touche pas (style, avertissement, outil absent du projet) n'est pas bloquant ; il est listé en réserve et ajouté comme tâche au plan. Seule une faille de sécurité critique ou haute préexistante dans la zone touchée reste bloquante.
4. **Classer chaque exigence** : validée, non testée, en échec, risque accepté (décision tracée de l'utilisateur pour un point bloquant, d'un agent arbitre pour un point non bloquant).
5. **Décider** : Accepté, Accepté sous réserve (points non bloquants listés), Refusé.
6. **En cas de refus**, pour chaque anomalie : exigence, preuve d'échec, agent responsable, attendu pour lever le refus.
7. **Après une correction**, refaire : la suite complète de tests et le lint (toujours), la revue du diff de la correction, et chaque contrôle spécialisé dont la zone a été touchée (sécurité, e2e, performance, design). La deuxième passe d'un agent de contrôle porte sur ce diff et sur ses anomalies précédentes, pas sur tout le livrable ; chaque agent de contrôle intervient au plus deux fois par parcours.

## Livrable
Le rapport de livraison défini dans le rôle `quality-gatekeeper`, avec la matrice :

```markdown
| Exigence | Tests | Parcours e2e | Preuve | Statut |
|----------|-------|--------------|--------|--------|
| US-03.1 Connexion valide | tests/Feature/LoginTest::valid | e2e/login.spec.ts | rapport e2e 2026-10-12 | validée |
| RG-02 5 tentatives / min | tests/Feature/LoginThrottleTest | — | `php artisan test` 214/214 | validée |
| US-03.4 Mot de passe oublié | — | — | — | non testée |
```

## Vérifications
- Les contrôles clés ont été ré-exécutés sur le commit livré, avec les commandes citées.
- Chaque règle bloquante applicable a un statut explicite.

## Limites
- Seul l'utilisateur peut accepter un risque bloquant ; le gatekeeper le trace, il ne le décide pas.

## En cas de blocage
- Rapport d'un agent de contrôle manquant : le demander avant de statuer, jamais le supposer favorable.
- Contrôle impossible à ré-exécuter alors que l'outil existe dans le projet : statut « non vérifié », qui empêche « Accepté » en profil livraison.
- Outil absent du projet (pas d'analyse statique, pas de e2e) : statut « non vérifié », réserve listée et tâche ajoutée au plan ; ce n'est ni un refus ni une décision humaine.
