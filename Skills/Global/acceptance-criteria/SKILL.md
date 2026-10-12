---
name: acceptance-criteria
description: Rédiger ou vérifier des critères d'acceptation testables (Given/When/Then), des règles métier identifiées (RG-xx), les erreurs et les cas limites d'une user story. À utiliser en cadrage, en planification pour le critère « terminé », et en validation pour confronter le résultat aux critères.
---

# Critères d'acceptation

## Quand l'utiliser
- `product-analyst` : écrire les critères de chaque story dans `docs/spec.md`.
- `planner` : dériver le critère « terminé » d'une tâche.
- `test-engineer`, `e2e-validator`, `quality-gatekeeper` : transformer les critères en tests et vérifier qu'ils sont tous couverts.

## Ce que l'agent rate sans ce skill
- Des critères invérifiables (« l'interface est intuitive », « c'est rapide »).
- Le seul chemin nominal : pas d'erreur, pas de droit refusé, pas de donnée vide ou limite.
- Des règles métier noyées dans le texte, sans identifiant, donc impossibles à tracer jusqu'aux tests.
- Des comportements inventés présentés comme des exigences.

## Entrées
- Le besoin exprimé par l'utilisateur, la spec existante, les sources visuelles éventuelles.

## Procédure
1. **Une story = un rôle, une action, une valeur** : « En tant que <rôle>, je veux <action> afin de <valeur> ». Priorité MoSCoW (Must, Should, Could, Won't).
2. **Extraire les règles métier** en phrases atomiques et numérotées (`RG-01`, `RG-02`…), réutilisables par plusieurs stories : seuils, calculs, statuts autorisés, unicité, délais.
3. **Écrire les critères en Given / When / Then**, un comportement par critère, avec des valeurs concrètes :
   > Given un client connecté avec un panier de 3 articles
   > When il valide la commande et le paiement est accepté
   > Then la commande passe au statut `payée`, le stock baisse de 3 et un e-mail de confirmation est envoyé (RG-04)
4. **Balayer systématiquement** ces familles de cas pour chaque story ; chaque cas pertinent devient un critère, chaque cas incertain une hypothèse :
   - nominal ;
   - entrée invalide ou manquante (format, longueur, valeur hors bornes) ;
   - droits : non connecté, rôle insuffisant, ressource d'un autre utilisateur ou d'une autre organisation ;
   - données vides, une seule, beaucoup (pagination, limites) ;
   - doublon et double soumission ;
   - concurrence (deux utilisateurs modifient la même ressource) ;
   - échec d'un service externe (paiement refusé, délai dépassé) ;
   - états de l'objet (une commande annulée peut-elle être payée ?) ;
   - temps : fuseaux, dates passées ou futures, expiration.
5. **Rendre mesurable le non fonctionnel** : performance (« liste de 1 000 commandes affichée en moins de 1 s au 95e centile »), accessibilité (niveau WCAG), compatibilité (navigateurs, versions mobiles).
6. **Séparer** ce qui est demandé de ce qui est supposé (section « Hypothèses », numérotées H-xx). Une règle absente de la demande se déduit selon le skill `autonomy-policy` (convention du produit, comportement le plus prudent pour les données et la sécurité) et devient une hypothèse avec sa raison. Seule une règle à portée légale, financière ou de conformité impossible à déduire devient une « Décision humaine requise ».

## Livrable
Dans `docs/spec.md`, pour chaque story : critères numérotés (`US-03.1`, `US-03.2`…), règles citées par identifiant, hypothèses et décisions humaines requises s'il y en a.

Pour un critère « terminé » de tâche : une phrase vérifiable par une commande ou un test, par exemple « 6e tentative de connexion en moins d'une minute → réponse 429, prouvé par `tests/Feature/LoginThrottleTest.php` ».

## Vérifications
- Chaque critère peut devenir un test automatisé ou un scénario e2e sans interprétation.
- Chaque règle métier est citée par au moins un critère ; chaque critère Must a au moins un cas d'erreur ou de droit associé quand c'est pertinent.

## Limites
- Une hypothèse n'est jamais présentée comme une exigence : elle reste marquée H-xx jusqu'à ce que l'utilisateur la confirme ou la corrige.

## En cas de blocage
- Règle ambiguë ou contradictoire : retiens l'interprétation la plus récente ou la plus précise, sinon la plus prudente, et consigne l'autre en hypothèse écartée avec ses conséquences.
