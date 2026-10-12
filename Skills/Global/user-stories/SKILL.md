---
name: user-stories
description: Transformer un besoin en user stories livrables indépendamment - rôles réels, carte des parcours, découpage vertical (INVEST, découpage par chemin, règle, donnée, interface), stories de cycle de vie oubliées, priorisation MoSCoW et MVP de bout en bout, identifiants stables. À utiliser pour écrire ou compléter les stories de docs/spec.md, ou pour redécouper une story trop grosse ; les critères d'acceptation relèvent du skill acceptance-criteria.
---

# User stories

La règle « une story = une valeur livrable indépendamment » est dans la procédure de `product-analyst` ; les zones floues deviennent des hypothèses selon le skill `autonomy-policy`. Ce skill donne la méthode pour trouver, découper et prioriser les stories. Leurs critères Given / When / Then relèvent du skill `acceptance-criteria`.

## Quand l'utiliser
- `product-analyst` : rédaction ou complément des stories de `docs/spec.md`.
- `planner` ou `orchestrator` : une story est trop grosse pour être découpée en tâches vérifiables (skill `task-breakdown`).

## Ce que l'agent rate sans ce skill
- Il écrit des tâches techniques déguisées : « En tant que développeur, je veux une table `orders` ». Aucune valeur pour un utilisateur, aucun critère vérifiable de l'extérieur.
- Il utilise « En tant qu'utilisateur » partout, alors que visiteur, client connecté et administrateur n'ont ni les mêmes droits ni les mêmes parcours.
- Il écrit un bénéfice tautologique (« je veux me connecter afin de me connecter »), qui ne permet plus de prioriser ni de trancher un cas limite.
- Il oublie les stories de cycle de vie : qui crée les données de départ, modifier, supprimer ou archiver, mot de passe oublié, désactivation d'un compte, export de ses données.
- Il découpe par couche (« toute l'API », puis « tous les écrans ») : le MVP n'est utilisable qu'à la fin.
- Il marque tout en Must, ce qui revient à ne pas prioriser.
- Il renumérote les US-xx en insérant une story, et casse la traçabilité avec le plan, les tests et le journal.

## Entrées
- La demande, les documents et sources visuelles fournis (skill `design-inputs`), `docs/spec.md` s'il existe, les écrans et routes d'un projet existant.

## Procédure
1. **Lister les rôles réels** : visiteur anonyme, utilisateur connecté, chaque rôle d'administration, systèmes externes (tâche planifiée, webhook entrant). Un rôle se distingue par des droits ou un parcours différents ; sinon ce n'en est pas un.
2. **Construire la carte des parcours** : pour chaque rôle, les activités (grands objectifs) en colonnes, puis les étapes de chaque activité. Chaque étape reçoit une ou plusieurs stories. Les trous de la carte (une étape sans story) sont les besoins oubliés.
3. **Balayer le cycle de vie de chaque objet métier** : création, consultation, liste et recherche, modification, suppression ou archivage, changement d'état, notification, export. Chaque opération pertinente devient une story ou une ligne du hors périmètre, jamais un oubli silencieux.
4. **Rédiger** : « En tant que <rôle précis>, je veux <action observable> afin de <bénéfice métier> ». Le bénéfice dit pourquoi, et sert à trancher les cas limites plus tard.
5. **Contrôler chaque story avec INVEST** : indépendante, négociable, porteuse de valeur, estimable, petite, testable. Signes qu'elle est trop grosse : plusieurs rôles, plus de 6 ou 7 critères, un « et » dans l'action, plusieurs écrans sans lien.
6. **Découper verticalement** une story trop grosse, en gardant chaque morceau utilisable seul :
   - **chemin** : le nominal d'abord, les variantes ensuite (paiement par carte, puis autres moyens) ;
   - **règle** : version simple de la règle, puis cas particuliers (frais de port fixes, puis par zone) ;
   - **donnée** : un type ou un format d'abord (import CSV, puis Excel) ;
   - **interface** : version minimale fonctionnelle, puis enrichissement (filtres, tri, export) ;
   - **inconnue technique** : tâche d'exploration bornée, qui relève du plan et pas de la spec.
7. **Écarter ce qui n'est pas une story** : contrainte non fonctionnelle (performance, accessibilité, compatibilité) → exigence rattachée aux stories concernées (skill `acceptance-criteria`) ; tâche technique → `docs/plan.md`.
8. **Prioriser en MoSCoW** : Must = sans elle le produit ne remplit pas sa promesse ou viole une règle légale ; Should = important mais contournable ; Could = confort ; Won't = exclu de cette version, recopié dans « Hors périmètre ». Repère : les Must ne dépassent pas environ 60 % des stories.
9. **Délimiter le MVP comme une tranche de bout en bout** de la carte : au moins une story par étape du parcours principal, pour que le premier livrable soit utilisable.
10. **Numéroter de façon stable** : `US-01`, `US-02`… dans l'ordre de création. Une story ajoutée prend le numéro suivant libre ; une story abandonnée reste listée avec le statut « abandonnée » et sa raison, son numéro n'est jamais réutilisé.

## Livrable
Dans `docs/spec.md`, section « User stories » :
```markdown
### Carte des parcours
| Rôle | Activité | Étapes | Stories |
|------|----------|--------|---------|
| Client | Commander | parcourir → panier → payer → suivre | US-03, US-04, US-05, US-07 |

### US-04 · Payer sa commande par carte (Must, MVP)
En tant que client connecté, je veux payer mon panier par carte afin de recevoir ma commande sans contact avec le vendeur.
Découpée de : US-04 initiale (paiement) ; variantes reportées : US-12 (autres moyens, Could).
Règles : RG-04, RG-05 · Hypothèses : H-03
Critères d'acceptation : (skill `acceptance-criteria`)
```

## Vérifications
- Chaque étape du parcours principal a au moins une story Must ou une ligne explicite du hors périmètre.
- Aucune story n'a « développeur » ou « système » pour seul bénéficiaire, ni de bénéfice qui répète l'action.
- Chaque objet métier a son cycle de vie traité (story ou hors périmètre).
- Les numéros existants sont inchangés (`git diff docs/spec.md` ne montre aucun US-xx renommé).

## Limites
- Pas d'estimation de délais ni de choix technique (périmètre de `product-analyst`).
- Une story ne décrit pas l'écran : la mise en page relève de `ui-ux-designer`.

## En cas de blocage
- Rôle ou parcours impossible à déduire : retiens le parcours le plus courant pour ce type de produit, consigne-le en hypothèse H-xx et continue.
- Story impossible à découper sans perdre sa valeur : garde-la entière, signale sa taille au `planner`, qui la découpe en tâches.
- Priorité contestée entre deux stories : le bénéfice écrit tranche ; si l'un des deux touche une obligation légale, il passe en Must.
