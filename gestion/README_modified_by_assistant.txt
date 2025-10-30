



Ajouts premium (valeur commerciale):
- Export CSV pour Clients, Véhicules, Contrats (accessible au staff) — utile pour reporting et intégration.
- Dashboard admin avec graphiques (Chart.js) montrant contrats par mois et occupation des véhicules.
- AuditLog simple (modèle + signaux) qui enregistre create/update/delete pour Client/Vehicule/Contrat.
- Liens rapides d'export depuis le dashboard.

Notes techniques:
- Pour que l'audit log enregistre l'utilisateur qui effectue l'action, il faudrait ajouter un middleware qui attache request.user aux modèles (ex: instance._last_actor) avant save/delete.
- Après pull du ZIP: exécuter makemigrations/migrate pour créer AuditLog.
