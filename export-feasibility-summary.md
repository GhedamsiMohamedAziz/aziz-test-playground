# Résumé — Faisabilité `aziz export`

Robin recommande de démarrer par une Option A (export client, pagination côté CLI, zéro changement backend) plutôt que par un endpoint dédié (B) ou un job asynchrone (C), en la concevant dès le départ pour migrer vers B plus tard sans casser le contrat de sortie — via un format stable (JSON/NDJSON) et un `manifest.json` versionné — les signaux de bascule vers B/C étant un export dépassant ~1-2 minutes ou des workspaces de plus d'une centaine de Mo.
