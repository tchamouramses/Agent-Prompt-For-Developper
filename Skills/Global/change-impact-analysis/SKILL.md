---
name: change-impact-analysis
description: Méthode détaillée pour identifier, avant une modification, tout ce qui dépend du code touché (appelants, contrats, données, comportements implicites) et évaluer le risque de régression. Complète la règle « Gestion des régressions » des principes des agents qui modifient du code.
---

# Analyse d'impact d'un changement

La règle est dans les principes des agents qui modifient du code (« Gestion des régressions ») : analyser avant de modifier, classer le risque, demander si le risque est possible ou probable. Ce skill donne la méthode pour le faire bien.

## Quand l'utiliser
- Avant de modifier une fonction, une classe, un composant, une route, un schéma, un événement ou une configuration utilisés ailleurs.
- Avant de supprimer du code présumé mort.

## Ce que l'agent rate sans ce skill
- Il cherche seulement les appels directs et rate les usages indirects : chaînes (noms de routes, de vues, de traductions, de jobs), réflexion, injection par conteneur, événements, templates, configuration, autres dépôts ou clients.
- Il change un format de réponse ou un comportement implicite (ordre, valeur par défaut, `null` contre absent, fuseau horaire) sans voir les consommateurs.
- Il juge le risque « faible » parce que les tests passent, alors que la zone n'est pas couverte.

## Entrées
- La tâche et la liste des éléments que tu prévois de modifier ou supprimer.

## Procédure
1. **Lister les éléments touchés** : symboles (fonctions, classes, méthodes, composants, types), contrats (routes, schémas d'API, événements, messages de file, commandes CLI), données (tables, colonnes, clés de cache, fichiers), configuration (variables d'environnement, clés de config, flags).
2. **Chercher les usages directs** de chaque élément dans tout le dépôt : recherche du nom exact, puis des variantes (casse, `snake_case` et `camelCase`, pluriel), imports et références de type.
3. **Chercher les usages indirects** :
   - noms passés en chaîne : routes nommées, vues et templates, clés de traduction, noms de jobs ou d'événements, sélecteurs de tests ;
   - liaisons dynamiques : conteneur d'injection, écouteurs déclarés en configuration, observers, middlewares, réflexion, `__call` ou proxys ;
   - consommateurs hors du code : front ou application mobile qui appelle l'API, autres services, webhooks sortants, tâches planifiées, exports, documentation publique ;
   - données existantes : lignes déjà en base, fichiers déjà stockés, entrées de cache, messages en file au moment du déploiement.
4. **Identifier les comportements implicites** qu'un consommateur peut attendre : forme exacte de la réponse, codes d'erreur, ordre de tri, valeurs par défaut, effets de bord (événement émis, e-mail envoyé), performance.
5. **Mesurer la couverture** : quels tests exercent ces usages ? Lance-les pour connaître l'état de départ. Un usage sans test compte comme non protégé.
6. **Classer le risque** :
   - **aucun** : élément nouveau ou privé sans autre usage ;
   - **faible** : tous les usages sont connus, adaptés dans le même changement et couverts par des tests ;
   - **possible** : un usage n'est pas couvert, ou un consommateur externe existe, ou des données existantes doivent rester lisibles ;
   - **probable** : un contrat public change, ou une migration de données irréversible, ou un comportement implicite change.
7. **Prévoir la protection** : adaptation des appelants dans le même changement, compatibilité ascendante (ancien champ conservé, alias, période de transition), test ajouté sur l'usage non couvert.

## Livrable
```markdown
### Impact
| Élément | Usages trouvés | Indirects / externes | Couvert par | Action |
|---------|----------------|----------------------|-------------|--------|
| `OrderResource::toArray` | 3 contrôleurs | app mobile (champ `total`) | tests/Feature/OrderApiTest | garder `total`, ajouter `total_ttc` |
Risque : possible (consommateur mobile hors dépôt), réduit à faible : `total` conservé et marqué obsolète, tâche T9 ajoutée au plan pour le retirer.
```

## Vérifications
- Chaque élément touché a été recherché en direct et en indirect ; les recherches lancées sont citées.
- Le risque correspond aux critères ci-dessus, pas à une impression.

## Limites
- Tu ne peux pas voir les dépôts externes : un consommateur externe probable suffit à classer le risque en « possible ».

## En cas de blocage
- Usage impossible à confirmer (chaîne construite dynamiquement, consommateur inconnu) : classer en « possible » et appliquer la protection la plus sûre (compatibilité ascendante, test sur l'usage supposé). Seule une rupture de contrat externe sans compatibilité possible devient une décision humaine.
