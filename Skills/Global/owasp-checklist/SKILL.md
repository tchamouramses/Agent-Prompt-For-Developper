---
name: owasp-checklist
description: Grille d'audit de sécurité indépendante du langage, alignée sur l'OWASP Top 10, l'OWASP API Security Top 10 et l'ASVS - inventaire des points d'entrée, questions par point d'entrée (accès à l'objet, aux propriétés et aux fonctions, injections, authentification, consommation de ressources, flux métier, configuration, erreurs, journaux), preuve par test sonde et barème de gravité. À utiliser pour auditer une fonctionnalité, un diff ou un projet, et pour relire du code qui touche aux droits ou aux données.
---

# Grille d'audit OWASP

L'agent `security-auditor` définit le périmètre et le format du rapport. Ce skill donne la grille appliquée à chaque point d'entrée, la façon de prouver une faille et le barème de gravité. Les failles et protections propres à un langage sont dans `security-<langage>` (par exemple le skill `security-php`).

## Quand l'utiliser
- `security-auditor` : tout audit, du correctif localisé au projet entier.
- `code-reviewer` : diff qui touche une route, une autorisation, une requête construite, un fichier, un appel sortant ou des données personnelles.
- Agents d'implémentation : avant de livrer une fonctionnalité qui expose des données.

## Ce que l'agent rate sans ce skill
- Il audite la route signalée et pas ses voisines : le correctif protège `show` mais `update`, `destroy`, l'export ou la recherche restent ouverts.
- Il vérifie le rôle mais pas l'objet : un utilisateur légitime agit sur la ressource d'un autre en changeant l'identifiant (BOLA ou IDOR).
- Il oublie le niveau des propriétés : une réponse qui expose des champs internes, ou une requête qui modifie un champ protégé (`role`, `owner_id`, `price`) par assignation de masse.
- Il oublie la consommation de ressources : taille de page non bornée, fichier ou corps de requête sans limite, absence de limitation de débit sur une route coûteuse.
- Il oublie les flux métier : rejouer un code promo, réserver tout le stock, contourner une étape d'un parcours en appelant directement la dernière route.
- Il rapporte une faille théorique sans scénario, ou classe « critique » ce qui demande un accès administrateur.
- Il ouvre `.env` pour vérifier une valeur, ou recopie un secret trouvé dans son rapport.

## Entrées
- Le périmètre (diff, fonctionnalité ou projet), la liste des routes et de leurs protections (`php artisan route:list`, `bin/console debug:router`, contrôleurs annotés, `app/api/**`), le modèle de droits, `docs/architecture.md`, les fichiers de dépendances verrouillés.

## Procédure
1. **Inventorier les points d'entrée** du périmètre, puis **élargir aux voisins** : toutes les actions sur la même ressource, les variantes (export, recherche, API mobile, ancienne version d'API), les tâches planifiées et files de messages qui traitent la même donnée, les webhooks entrants.
2. **Pour chaque point d'entrée, répondre à la grille** :

| Thème | Question | Signe d'une faille |
|-------|----------|--------------------|
| Accès à l'objet (BOLA) | L'identifiant reçu est-il vérifié contre l'utilisateur ou le tenant courant ? | `find($id)` sans filtre ni policy ; liste non filtrée par propriétaire |
| Accès aux propriétés | Quels champs sont lus et écrits ? | sérialisation du modèle entier ; assignation de masse sans liste blanche |
| Accès aux fonctions | Le rôle requis est-il vérifié côté serveur ? | route d'administration protégée seulement par un menu caché |
| Authentification | Qui peut appeler sans session ou jeton ? Durée et révocation du jeton ? | route publique par oubli ; jeton sans expiration |
| Injections | Une donnée reçue atteint-elle une requête, une commande, un template, un en-tête, un chemin de fichier ? | concaténation ; nom de colonne ou de tri venant de la requête |
| Ressources | Taille de page, de corps, de fichier, nombre d'éléments, coût d'une requête bornés ? Débit limité ? | `per_page` libre ; envoi de fichier sans taille max ; recherche non indexée |
| Flux métier | L'action peut-elle être rejouée, automatisée, appelée hors ordre ? | code à usage unique réutilisable ; étape de paiement sautée |
| Appels sortants (SSRF) | Une URL reçue est-elle appelée côté serveur ? | aperçu de lien ou webhook vers une adresse interne |
| Erreurs | Une exception renvoie-t-elle des détails ? L'erreur laisse-t-elle passer (fail open) ? | trace en réponse ; `catch` qui autorise par défaut |
| Configuration | Debug, CORS, en-têtes, cookies, CSRF conformes en production ? | `*` en origine avec cookies ; debug activé |
| Journaux | Les refus et actions sensibles sont-ils tracés, sans secret ni donnée personnelle inutile ? | mot de passe ou jeton journalisé ; aucune trace des refus |
| Intégrité | Les données reçues d'un tiers (webhook, fichier, mise à jour) sont-elles vérifiées ? | webhook sans signature ; désérialisation d'objets externes |

3. **Contrôles transverses** une fois par audit :
   - dépendances : audit de l'écosystème et vulnérabilités hautes ou critiques ;
   - secrets : présence dans le code et l'historique (skill `env-secrets`) ;
   - configuration de production : vérifiée sans lire `.env`, à partir de `.env.example`, de la configuration versionnée ou des commandes du framework qui affichent la configuration chargée.
4. **Prouver chaque faille suspectée** par un test sonde écrit dans `/tmp` ou une requête rejouable, qui montre l'accès obtenu : statut, données reçues. Tu ne modifies pas le dépôt. Sans preuve, le constat est classé « à confirmer » avec ce qui manque pour le prouver.
5. **Classer** selon le barème :

| Gravité | Critère |
|---------|---------|
| Critique | sans compte ou par un compte quelconque : exécution de code, lecture ou modification des données de tous les utilisateurs, secret de production exposé |
| Haute | un utilisateur authentifié accède aux données ou actions d'un autre, ou s'élève en privilège ; contournement d'un paiement |
| Moyenne | exploitation sous conditions (interaction de la victime, information préalable), déni de service par un utilisateur, fuite d'information limitée |
| Basse | défense en profondeur absente sans exploitation démontrée (en-tête manquant, message d'erreur trop détaillé) |

6. **Pour chaque faille, proposer la correction au bon niveau** : policy ou filtre de requête plutôt que vérification dans la vue, liste blanche plutôt que liste noire, borne côté serveur plutôt que côté client. Indique le test qui prouvera la correction.

## Livrable
Le rapport défini dans le rôle `security-auditor`. Chaque constat donne :
- l'emplacement `fichier:ligne` ;
- le thème de la grille ;
- le scénario d'exploitation ;
- la preuve (test sonde ou requête, et résultat) ;
- la gravité ;
- la correction et son test.

La section « Points vérifiés sans anomalie » liste les thèmes passés pour chaque point d'entrée.

## Vérifications
- Chaque point d'entrée du périmètre et chaque voisin inventorié a une ligne par thème applicable dans le rapport.
- Chaque faille haute ou critique a une preuve exécutée.
- L'audit des dépendances a été lancé et son résultat est cité.
- Aucun secret n'apparaît dans le rapport, ni dans les commandes citées.

## Limites
- Analyse du code et tests locaux seulement : aucun test contre un système distant ou de production.
- Pour un niveau de vérification plus poussé (applications financières, de santé), la référence est l'OWASP ASVS niveau 2 ou 3 ; ce skill couvre l'essentiel du niveau 1 et les points les plus exploités du niveau 2.
- Les questions juridiques (données personnelles, conservation) restent des décisions humaines (règle 5 des principes communs).

## En cas de blocage
- Application impossible à lancer pour un test sonde : rapporte le constat « à confirmer » avec le chemin de code qui y mène, et renvoie le démarrage à `devops-engineer`.
- Secret réel découvert : décision humaine immédiate (rotation, nettoyage de l'historique), sans l'afficher ; indique seulement le fichier et le type de secret.
- Faille dont la correction change un contrat consommé hors du dépôt : propose la correction la plus forte compatible et signale le risque restant comme bloquant.
