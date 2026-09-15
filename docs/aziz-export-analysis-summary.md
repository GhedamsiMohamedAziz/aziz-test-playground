# Résumé : faisabilité `aziz export`

Analyse complète : `robin-analysis.md` (non commitée, brouillon de travail).

## Recommandation de Robin

Livrer l'option B — une archive versionnée (JSONL par entité + `manifest.json` avec
`schema_version`, streaming, secrets exclus par défaut, filtre `--since`) — plutôt que le
dump JSON brut (A, plus rapide mais couplé au schéma interne) ou l'export serveur
asynchrone (C, surdimensionné sans volumes mesurés).

## Étapes proposées

1. MVP JSONL + manifest, streaming, exclusion des secrets, `--since`.
2. Tests : aller-retour export/relecture, cohérence du manifest et des comptes, absence de
   secrets, borne mémoire sur un jeu de données volumineux.
3. CSV et `aziz import` plus tard, seulement sur demande utilisateur.

## À vérifier avant de coder

Lire la couche données du CLI pour confirmer que l'accès existant (API ou stockage local)
peut être réutilisé sans changement majeur. Si l'accès ne passe que par une API paginée, il
faudra ajouter la reprise sur erreur au MVP.

## Limite de cette analyse

Faite sans accès au code source du CLI (workspace vide au moment de l'analyse) : à valider
par quelqu'un qui connaît la base de code avant de lancer l'implémentation.
