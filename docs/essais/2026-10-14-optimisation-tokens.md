# Essai : coût et durée avant et après l'optimisation des tokens (2026-10-14)

## Montage
- Projet jetable : Laravel 13.36 (squelette du jour, PHPUnit 12, SQLite), une copie par variante.
- Bibliothèque installée avec `node scripts/install.mjs <projet> --stack laravel --outil claude` (20 agents, 62 skills).
- Même demande pour toutes les variantes : API REST de notes personnelles (jetons Sanctum, CRUD, archivage, liste paginée filtrable, chaque utilisateur limité à ses notes), sur une branche de travail, sans fusion.
- Lancement : `claude -p "<demande>" --agent orchestrator --model sonnet --permission-mode bypassPermissions --output-format stream-json`, configuration Claude Code vierge, effort de session `medium`.
- Coût au tarif public tel que rapporté par Claude Code (`total_cost_usd`). Une seule exécution par variante : l'écart d'une exécution à l'autre reste important.

## Résultats

| Variante | Coût | Durée | Appels d'agents | Tests | Pint |
|---|---|---|---|---|---|
| Avant (`main`) | 4,70 $ | 21,4 min | 8 : implémentation ×3, revue ×2, sécurité ×2, doc | 64 verts | conforme |
| 1. Modèles fixés, préchargements allégés, sorties compactes | 4,19 $ | 22,4 min | 7 | 78 verts | conforme |
| 2. + outil `Skill` retiré | 3,61 $ | 16,6 min | 8 | 51 verts | conforme |
| 3. + contrôles en parallèle, effort par agent | 3,59 $ | 18,6 min | 7 | 57 verts | conforme |
| 4. + lancement parallèle explicite | 4,30 $ | 21,0 min | 8 | 64 verts | conforme |
| 5. + deuxième passe réservée aux points bloquants | 2,27 $ | 11,3 min | 7 : implémentation ×3, revue ×2, sécurité ×1, doc | 52 verts | conforme |
| 6. + doc-writer en parallèle, durcissement d'authentification dans `security-php` | 2,32 $ | 10,4 min | 5 (doc-writer sauté par erreur) | 52 verts | conforme |
| 7. + durcissement détaillé | arrêté | plus lent | implémentation de près de 6 min par appel | | |
| 8. Profil léger court : une passe, doc-writer avec les contrôles, correction seulement si bloquant | 2,34 $ | 11,2 min | 6 | 49 verts | conforme |
| 9. + 500 des API Laravel sans `Accept` évité, correction légère limitée aux bloquants | **1,96 $** | **8,2 min** | 4 : implémentation, revue, sécurité et doc en parallèle | 53 verts | conforme |

Variante 9 par rapport à `main` : **-58 % de coût, -62 % de durée**. Revue de code et audit de sécurité sont toujours faits, et les tests sont verts.

Contrepartie du profil léger court (variantes 8 et 9) : les points non bloquants ne sont plus corrigés dans le parcours. Dans la variante 9, il reste 2 failles moyennes et 4 basses, aucune critique ni haute ; elles sont notées dans `docs/plan.md` et le bilan, et se corrigent sur demande. Le profil livraison les corrige toujours.

## Ce que les mesures ont montré
- **Contexte de départ des agents** (tokens au premier tour) : `laravel-implementer` passe de 65 000 à 45 000, `code-reviewer` de 17 000 à 12 000 et `security-auditor` de 25 000 à 20 000.
- **L'outil `Skill` coûte cher.** Il ajoute à chaque agent la liste de tous les skills installés : +6 000 à +12 000 tokens à chaque tour. La variante 1 l'avait ajouté pour le chargement à la demande, ce qui annulait une partie du gain. Les skills hors en-tête sont maintenant lus avec `Read`.
- **`security-auditor` (Opus) est le plus long** : 3 à 5 minutes par passe, et 35 à 42 % du coût. Avant la variante 5, il était relancé après des corrections de points non bloquants (failles moyennes), et un troisième appel d'implémentation traitait des points bas.
- **Contrôles en parallèle** : l'orchestrateur lance bien la revue et l'audit ensemble depuis la variante 4. Le gain reste modeste, car la revue est courte (environ 50 s) à côté de l'audit.
- **Effort** : en `high`, `security-auditor` a pris environ 290 s par passe, contre 225 s en `medium`, avec des constats du même ordre. Il est donc en `medium`.

- **Prévenir coûte moins que corriger.** Un point bloquant récurrent (500 au lieu de 401 sur une API Laravel appelée sans `Accept`) déclenchait à lui seul un cycle correction + revue d'environ 3 minutes. Une ligne dans le skill `laravel` l'évite. À l'inverse, une liste de durcissement trop détaillée a doublé la durée de l'implémentation (variante 7) : elle a été retirée.

## Limites
- Une seule exécution par variante, une seule stack, une fonctionnalité d'une seule application (profil léger).
- Toutes les variantes ont tourné avec une session Sonnet. Si la session tourne sur Opus, `main` coûte plus cher, car 20 agents y héritent du modèle de la session ; le gain réel est alors plus grand que celui mesuré ici.
