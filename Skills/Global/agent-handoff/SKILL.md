---
name: agent-handoff
description: Gabarits pour transmettre le travail entre agents sans perte - le brief qu'on donne à un agent, le compte rendu qu'il rend, la reprise après une question ou un refus. À utiliser par l'orchestrateur ou toute session qui lance un agent, et par un agent qui rend la main.
---

# Passage de relais entre agents

Les règles sont dans les principes communs (poser une question, compte rendu) et dans le rôle de l'orchestrateur (briefer, séparer production et contrôle). Ce skill donne les gabarits complets.

## Quand l'utiliser
- Avant de lancer un agent : rédiger le brief.
- En fin de travail d'un agent : rédiger le compte rendu.
- Pour relancer un agent après une question à l'utilisateur ou un refus d'un agent de contrôle.

## Ce que l'agent rate sans ce skill
- Un brief qui suppose que l'agent a vu la conversation : l'agent lancé ne voit **que** son brief.
- Des décisions déjà prises qui ne sont pas transmises, donc reposées ou contredites.
- Un agent de contrôle qui reçoit l'avis du producteur (« tout marche, j'ai testé ») et perd son indépendance.
- Une relance qui oublie ce qui était déjà fait, d'où du travail refait ou cassé.

## Entrées
- La tâche, les décisions déjà prises, le compte rendu précédent en cas de relance.

## Procédure
1. Avant de lancer un agent, remplis le brief ci-dessous ; pour un agent de contrôle, applique la règle d'indépendance.
2. En fin de travail, l'agent lancé rend le compte rendu ci-dessous.
3. Après une question à l'utilisateur ou un refus, relance avec le gabarit correspondant.

### Brief d'un agent
```markdown
**Objectif :** <une phrase, résultat attendu, pas la méthode>
**Contexte à lire :** <fichiers précis et sections : docs/spec.md US-03, docs/plan.md T4, dossiers de code>
**Décisions déjà prises :** <choix de l'utilisateur avec leur source : journal du AAAA-MM-JJ, ADR-0004>
**Livrable :** <fichiers à produire ou modifier, compte rendu, entrée de journal>
**Critère de fin :** <vérifiable : test, commande, comportement>
**Limites :** <ce qu'il ne doit pas toucher, pas de nouvelle dépendance, zone interdite>
**Profil :** <léger ou livraison>
```

Pour un agent de contrôle, ajoute « Livrable à contrôler : <diff, branche ou fichiers> » et n'inclus **ni** le compte rendu ni l'avis de l'agent producteur, seulement la spec, le plan et le livrable.

### Compte rendu d'un agent
Le format des principes communs (Fait, Vérifié, Régressions, Reste à faire / questions), plus si besoin :
- **Question pour l'utilisateur** (format des principes communs) ;
- **Fichiers à enregistrer** pour un agent sans outil d'écriture : chemin puis contenu ;
- **Entrée de journal** prête à enregistrer (skill `project-docs-tracking`).

### Relance après une question
```markdown
**Reprise de :** <agent>, brief du <date ou identifiant>
**Réponse de l'utilisateur :** <citation exacte et option choisie>
**Déjà fait lors du premier passage :** <résumé du compte rendu précédent, fichiers déjà modifiés>
**Reste à faire :** <ce qui dépendait de la réponse>
```

### Relance après un refus
```markdown
**Refus de :** <agent de contrôle>, rapport <chemin>
**Anomalies à traiter :**
1. <exigence> — preuve d'échec : <commande et sortie, capture> — attendu : <…>
**Ne pas modifier :** <ce qui a été validé>
**Preuve attendue en retour :** pour chaque anomalie, ce qui a changé et la nouvelle preuve
```

## Livrable
- Le brief, le compte rendu ou la relance, complets selon les gabarits.

## Vérifications
- Le brief se comprend sans la conversation : relis-le comme si tu ne savais rien d'autre.
- Toute décision déjà prise qui touche la tâche y figure avec sa source.

## Limites
- Le brief ne dicte pas la méthode de l'agent : il fixe l'objectif, le contexte et les limites.

## En cas de blocage
- Un compte rendu incomplet (pas de preuve, pas de critère vérifié) : renvoie-le à l'agent avec ce qui manque plutôt que de compléter à sa place.
