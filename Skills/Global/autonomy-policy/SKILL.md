---
name: autonomy-policy
description: Décider sans solliciter l'humain - classer chaque décision (décider seul, décider et signaler, réservé à l'humain), choisir un défaut sûr quand une information manque, arbitrer entre agents, consigner les décisions et regrouper les rares demandes humaines. Complète la règle « Autonomie et escalade » des principes communs.
---

# Politique d'autonomie

La règle est dans les principes communs (« Autonomie et escalade », « Actions réservées à l'humain ») : l'agent décide et avance ; seules les actions réservées attendent un humain. Ce skill donne la méthode de classement, de choix par défaut et de consignation.

## Quand l'utiliser
- Chaque fois qu'une information manque, qu'un choix se présente ou qu'un agent hésite à demander.
- `orchestrator` : pour arbitrer, regrouper les demandes humaines et rédiger le bilan.

## Ce que l'agent rate sans ce skill
- Il s'arrête pour demander ce qu'il pouvait décider seul (nom d'une variable, librairie gratuite standard, cas limite évident), et le projet reste bloqué des heures.
- À l'inverse, il prend seul une décision irréversible ou coûteuse (déploiement, suppression de données réelles, service payant).
- Il décide sans laisser de trace : personne ne sait plus pourquoi ce choix a été fait.
- Il pose les questions une par une au lieu de les regrouper.

## Entrées
- La décision à prendre, la spec, l'architecture, les décisions déjà consignées (journal, ADR).

## Procédure

### 1. Classer la décision
| Niveau | Quand | Exemples |
|--------|-------|----------|
| **Décider seul** | réversible, sans coût, sans effet hors du dépôt, et une option raisonnable se dégage | nommage, structure interne, choix entre deux implémentations, cas limite non spécifié mais évident, librairie gratuite à licence permissive, ajout de tests, refactoring dans le périmètre, branche, commit, push de la branche, ouverture de PR |
| **Décider et signaler** | réversible mais visible par l'utilisateur ou le client, ou hypothèse sur le métier | règle métier déduite de la spec, libellé ou message affiché, choix visuel non couvert par la maquette, stack ou pattern d'architecture, compatibilité ascendante conservée temporairement, risque de régression réduit puis accepté |
| **Réservé à l'humain** | irréversible, coûteux, hors du dépôt, légal, ou impossible à déduire | voir la règle « Actions réservées à l'humain » des principes communs |

En cas de doute entre deux niveaux, prends le plus autonome **si** l'action reste réversible ; sinon le plus prudent.

### 2. Choisir le défaut quand une information manque
Dans l'ordre, retiens la première source qui répond :
1. une décision déjà consignée (journal, ADR, spec, plan) ;
2. la convention déjà en place dans le projet ;
3. le comportement natif ou recommandé du framework ;
4. la pratique la plus répandue et la plus sûre (sécurité par défaut, données préservées, compatibilité conservée) ;
5. l'option la plus simple à annuler plus tard.

Écris le choix comme hypothèse vérifiable : « Hypothèse H-03 : un utilisateur désactivé ne peut plus se connecter mais ses commandes restent visibles par l'administrateur (convention des autres entités) ».

### 3. Arbitrer un désaccord entre agents sans l'humain
- D'abord les preuves : test, mesure, extrait de spec.
- Puis l'arbitre du domaine : `product-analyst` pour le fonctionnel, `architect` pour la conception, `security-auditor` pour la sécurité, `quality-gatekeeper` pour l'acceptation.
- L'humain seulement si l'arbitrage touche une action réservée, ou si le même désaccord revient après l'arbitrage.

### 4. Choisir une librairie seul
Après avoir vérifié que le besoin n'est pas couvert par le langage, le framework ou une dépendance présente, compare 2 ou 3 candidats et retiens celui qui satisfait tous ces critères :
- licence permissive (MIT, Apache-2.0, BSD, ISC, MPL-2.0 acceptable pour un usage non modifié) ;
- maintenue : version publiée dans les 12 derniers mois, tickets traités ;
- compatible avec les versions installées (skill `version-compatibility`) ;
- largement adoptée dans l'écosystème, sans vulnérabilité connue non corrigée ;
- poids et dépendances transitives proportionnés au besoin.
Installe-la avec le gestionnaire du projet, version verrouillée, et consigne la comparaison (journal, ou ADR si elle structure le projet). Si aucun candidat ne passe les critères, ou si le seul candidat est payant ou sous licence restrictive, c'est une action réservée.

### 5. Consigner
- Chaque décision « signaler » et chaque choix de librairie : une ligne dans la section « Décisions » de l'entrée de journal (skill `project-docs-tracking`), avec la raison et la façon d'annuler.
- Chaque décision structurante : un ADR.
- Le compte rendu liste les décisions prises seul dans « Décisions prises ».

### 6. Regrouper les demandes humaines
- **Filtre d'abord** : une demande humaine correspond à une ligne de la règle 5 des principes communs, sinon ce n'en est pas une. Accepter un risque non bloquant, choisir un flux fonctionnel non précisé, ajouter un outil de qualité ou corriger un défaut préexistant se décident par l'agent arbitre (section 3) et se consignent dans « Décisions prises » ou comme tâche du plan.
- Ne bloque que ce qui dépend de l'action réservée ; termine tout le reste.
- Prépare l'action pour que l'humain n'ait qu'à dire oui : commande exacte, diff, plan de retour arrière, coût.
- L'orchestrateur rassemble toutes les demandes en un seul message, au moment où elles bloquent la suite ou à la fin du parcours :

```markdown
**Décisions humaines requises (2)**
1. Fusionner la PR #12 dans main — prête : CI verte, gatekeeper « Accepté ». Retour arrière : revert du commit de fusion.
2. Créer un compte chez le fournisseur d'e-mails (offre gratuite jusqu'à 3 000 e-mails/mois, puis payant) — alternative sans coût : SMTP existant de l'entreprise.
Ma recommandation : 1) oui ; 2) SMTP existant.
```

## Livrable
- La décision prise et consignée, ou la demande humaine préparée selon le gabarit ci-dessus.

## Vérifications
- Aucune action réservée n'a été faite sans accord humain tracé.
- Chaque décision « signaler » apparaît dans le journal et dans le compte rendu.

## Limites
- L'autonomie ne couvre jamais l'affaiblissement d'un contrôle : désactiver un test, une étape de CI ou une vérification de sécurité pour avancer reste interdit.

## En cas de blocage
- Toute la suite dépend d'une action réservée : livre ce qui est fait, la demande préparée, et arrête-toi proprement.
