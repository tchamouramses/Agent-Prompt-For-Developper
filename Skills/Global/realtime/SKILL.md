---
name: realtime
description: Concevoir et coder les fonctionnalités temps réel (notifications instantanées, tableaux de bord en direct, chat, présence, édition collaborative simple) - choix entre interrogation périodique, Server-Sent Events et WebSocket, autorisation des canaux, diffusion après commit, reconnexion et resynchronisation, montée en charge et tests. À utiliser dès qu'un écran doit se mettre à jour sans action de l'utilisateur.
---

# Temps réel

Une connexion temps réel reste ouverte, se coupe, se reconnecte, et passe souvent hors des protections habituelles des requêtes HTTP. Ce skill évite les trois erreurs courantes : une technologie trop lourde pour le besoin, des canaux que n'importe qui peut écouter, et un client qui perd des événements à chaque coupure.

## Quand l'utiliser
- La spec demande une mise à jour sans rechargement : notification, statut qui évolue, compteur, chat, présence, suivi d'un traitement long.
- Ajouter un canal, un événement diffusé ou un abonnement côté client.
- `architect` : choisir la technologie et le serveur de diffusion.

## Ce que l'agent rate sans ce skill
- Il installe un serveur WebSocket pour un statut qui change toutes les trente secondes, où une interrogation périodique suffisait.
- Il diffuse sur un canal public des données privées, ou autorise un canal privé sans vérifier que l'utilisateur a droit à la ressource (ou au tenant).
- Il diffuse l'événement avant le commit de la transaction : le client recharge et ne trouve pas la donnée.
- Le client ne gère pas la reconnexion ni les événements manqués pendant la coupure, et l'écran reste faux sans que l'utilisateur le sache.
- Il envoie l'objet complet dans l'événement, données sensibles comprises.

## Entrées
- `docs/spec.md` (fraîcheur attendue, nombre d'utilisateurs connectés), `docs/architecture.md`, l'outillage temps réel déjà présent dans le projet.

## Procédure

### 1. Choisir la technologie la plus simple qui tient le besoin
| Besoin | Choix par défaut |
|--------|------------------|
| Fraîcheur de l'ordre de 10 secondes ou plus, peu d'écrans | interrogation périodique (avec arrêt quand l'onglet est caché) |
| Le serveur pousse, le client ne fait qu'écouter (notifications, progression, tableau de bord) | Server-Sent Events (SSE) |
| Échanges dans les deux sens à faible latence (chat, présence, collaboration) | WebSocket |

Outils natifs ou standards de chaque stack, à préférer à une librairie extérieure : Laravel Broadcasting avec Reverb ; Symfony Mercure (SSE) ; Spring WebSocket avec STOMP, ou `SseEmitter` ; côté Node, le support natif SSE ou une librairie WebSocket répandue. Côté client : `EventSource` pour SSE, le client fourni par l'outil serveur pour WebSocket (Laravel Echo, client STOMP…). Un service hébergé payant (Pusher, Ably…) est une action réservée (coût, compte chez un tiers) : prépare la configuration, propose l'alternative auto-hébergée.

Le choix est consigné en ADR avec le nombre de connexions simultanées attendu.

### 2. Nommer et autoriser les canaux
- Canal public seulement pour une donnée publique. Toute donnée d'un utilisateur, d'une ressource ou d'un tenant passe par un canal privé dont le nom identifie la ressource (`commande.{id}`, `tenant.{tenantId}.tableau`).
- L'autorisation d'un canal privé applique la même règle que la lecture HTTP de la ressource (même Policy, voter ou contrôle d'accès), et vérifie le tenant (skill `multi-tenancy`).
- La connexion est authentifiée (cookie de session ou jeton à courte durée) ; un jeton n'est jamais placé dans une URL journalisée sans être à usage unique ou très court.

### 3. Diffuser correctement
- La diffusion part **après** le commit de la transaction qui a produit le changement (même règle que les tâches en file, skill `background-jobs-events`), et de préférence depuis une file pour ne pas ralentir la requête.
- L'événement contient l'identifiant, le type de changement et un numéro de version ou un horodatage ; le client recharge le détail par l'API s'il en a besoin. Aucune donnée qu'un abonné autorisé ne pourrait pas lire par l'API.
- L'auteur d'un changement ne doit pas appliquer deux fois son propre changement (exclure l'émetteur, ou ignorer un événement dont la version est déjà connue).

### 4. Reconnexion et resynchronisation côté client
- Reconnexion automatique avec délai croissant ; indicateur visible quand la connexion est perdue depuis plus de quelques secondes.
- À la reconnexion, le client se resynchronise : il recharge l'état par l'API, ou demande les événements manqués (`Last-Event-ID` en SSE, numéro de version). Il ne suppose jamais avoir tout reçu.
- Les événements sont appliqués selon leur version ; un événement plus ancien que l'état connu est ignoré.
- Abonnement fermé quand l'écran est quitté (pas de fuite de connexions ni d'écouteurs).

### 5. Exploitation
- Plusieurs instances du serveur : la diffusion passe par un relais commun (Redis pub/sub ou le serveur de diffusion dédié), et la répartition de charge supporte les connexions longues (WebSocket : mise à niveau HTTP autorisée, délais d'inactivité adaptés).
- Limiter le nombre de connexions et la taille des messages par utilisateur ; journaliser les refus d'autorisation de canal.
- Les commandes pour lancer le serveur de diffusion en local et en production vont dans `docs/runbook.md`.

### 6. Tester
- Côté serveur : l'événement est diffusé après le commit, sur le bon canal, avec le contenu attendu (faux de diffusion du framework) ; l'autorisation du canal refuse un utilisateur sans droit et un utilisateur d'un autre tenant.
- Côté client : l'écran applique un événement reçu, ignore un événement périmé, et se resynchronise après une reconnexion (test de composant avec une connexion simulée).
- Un parcours de bout en bout avec deux sessions, si l'outil E2E du projet le permet (skill `e2e-testing`).

## Livrable
- La fonctionnalité temps réel avec technologie justifiée, canaux autorisés, diffusion après commit, resynchronisation, tests de l'étape 6.
- `architect` : la section « Temps réel » de `docs/architecture.md` (technologie, serveur, canaux, conventions d'événements) et l'ADR.

## Vérifications
- Le test d'autorisation des canaux privés passe, y compris le cas d'un autre tenant.
- Aucun événement diffusé dans une transaction sans report après commit (recherche dans le diff).
- Le client a un test de resynchronisation après reconnexion.

## Limites
- L'édition collaborative avancée (fusion de modifications concurrentes, CRDT) demande un ADR à part et une librairie spécialisée.
- Les notifications push mobiles (APNs, FCM) ne sont pas du temps réel au sens de ce skill ; elles relèvent du skill du framework mobile.

## En cas de blocage
- Serveur de diffusion impossible à lancer dans l'environnement de test : tester la diffusion avec le faux du framework et le client avec une connexion simulée ; marquer la connexion réelle **non vérifiée**.
- Besoin de fraîcheur flou : retenir l'interrogation périodique, la plus simple à remplacer, et consigner l'hypothèse.
