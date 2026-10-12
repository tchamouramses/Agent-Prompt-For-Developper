---
name: code-review-checklist
description: Checklist détaillée pour relire un changement (diff, branche ou PR) - correction, régressions, contrats, sécurité évidente, tests, SOLID, duplication, code mort, lisibilité - avec des exemples de défauts fréquents et un barème de gravité. À utiliser par code-reviewer et par tout agent qui relit son propre diff.
---

# Checklist de revue de code

## Quand l'utiliser
- `code-reviewer` : revue d'un changement produit par un autre agent.
- Agents d'implémentation : relecture de leur propre diff avant de rendre la main (cela ne remplace pas la revue indépendante).

## Ce que l'agent rate sans ce skill
- Il relit seulement les lignes modifiées, pas leur contexte ni leurs appelants.
- Il commente le style et rate le bug.
- Il présente une préférence comme un défaut bloquant, ou laisse passer un vrai défaut en « suggestion ».
- Il fait confiance au compte rendu du producteur au lieu de vérifier.

## Entrées
- Le diff (`git diff <base>...HEAD`), la tâche, les critères d'acceptation, les conventions du projet.

## Procédure
1. Lis la tâche et les critères, puis **tout le diff**, puis le code autour de chaque changement et ses appelants.
2. Lance le lint, l'analyse statique et les tests de la zone ; cite les commandes et résultats.
3. Passe chaque section ci-dessous. Pour chaque défaut : `fichier:ligne`, problème, conséquence concrète, correction proposée.

### Correction
- Cas limites : `null`, liste vide, zéro, valeurs négatives, chaînes vides, très grandes entrées.
- Erreurs : exceptions avalées, `catch` trop large, erreur retournée mais ignorée, message d'erreur qui fuit des détails internes.
- Concurrence : lecture puis écriture sans verrou ni contrainte d'unicité, double soumission, job relancé deux fois.
- Données : écritures multiples hors transaction, conversion de type ou d'arrondi (argent en flottant), fuseau horaire.
- Asynchrone : promesse non attendue, effet de bord dans un rendu, abonnement jamais libéré.

### Régressions et contrats
- Appelants du code modifié non adaptés ; signature, format de réponse, code HTTP, événement ou colonne modifiés sans compatibilité (méthode du skill `change-impact-analysis`).
- Migration irréversible ou destructrice, sans plan de retour.

### Conformité
- Chaque critère d'acceptation de la tâche est implémenté et testé ; rien de hors périmètre n'a été ajouté.

### Sécurité évidente
- Entrée non validée, autorisation vérifiée sur le rôle mais pas sur la ressource, requête construite par concaténation, sortie non échappée, secret dans le code ou les logs, upload non contrôlé. Doute sérieux → `security-auditor`.

### Tests
- Ils testent le comportement, pas l'implémentation ; ils échoueraient si le comportement disparaissait ; ils couvrent erreurs et droits (skill `testing-strategy`). Aucun test supprimé, sauté ou affaibli.

### Conception (SOLID)
- Responsabilité unique : contrôleur ou composant qui fait accès aux données, logique métier et présentation à la fois.
- Ouvert / fermé : nouvelle variante ajoutée en allongeant un `switch` déjà long.
- Substitution : implémentation qui lève une exception ou ignore un paramètre du contrat parent.
- Interfaces : client forcé de dépendre de méthodes qu'il n'utilise pas.
- Dépendances : logique métier qui instancie l'infrastructure (client HTTP, accès direct à la base, appel statique) au lieu de la recevoir.
- À l'inverse : abstraction sans usage réel (interface à une implémentation sans raison, couche « pour plus tard ») = défaut aussi.

### Duplication et code mort
- Logique recopiée alors qu'un utilitaire existe ; ancienne version laissée après remplacement ; imports, variables, fonctions, routes, styles, fichiers, dépendances inutilisés ; code commenté ; `TODO` sans tâche.

### Lisibilité et conventions
- Nommage, taille des fonctions, imbrication, conventions du projet (pas les tiennes).

### Dépendances
- Toute dépendance ajoutée respecte les critères du skill `autonomy-policy` (licence, maintenance, compatibilité, adoption, vulnérabilités, poids) et sa comparaison est consignée (journal ou ADR).

4. **Classer** :
   - **Bloquant** : bug, régression, faille, perte de données, critère non respecté, test manquant sur un comportement critique, dépendance hors critères ou sans comparaison consignée.
   - **Important** : duplication, code mort, violation SOLID qui gêne déjà la maintenance, test fragile.
   - **Suggestion** : nommage, style, amélioration facultative. Une préférence n'est jamais bloquante.

## Livrable
Le rapport défini dans le rôle `code-reviewer` (verdict, vérifications, Bloquant, Important, Suggestion, Points positifs).

## Vérifications
- Tout le diff a été lu ; chaque remarque bloquante a une conséquence concrète et une correction.

## Limites
- Pas de réécriture du code : la revue propose, l'agent producteur corrige.

## En cas de blocage
- Diff trop gros pour une revue fiable : le dire et proposer un découpage, ou relire par lots en l'annonçant.
