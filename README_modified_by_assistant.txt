Modifications apportées par l'assistant:
- Design:
  * Ajout d'un fichier static/css/theme.css avec un thème moderne (palette, boutons, ombres, typographie Inter).
  * Inclusion de Google Fonts (Inter) et du CSS dans templates/gestion/base.html.
- Fonctionnalités / Sécurité:
  * Les boutons d'ajout/modification/suppression dans les templates publiques ont été entourés d'une vérification {% if request.user.is_staff %} pour n'être visibles que pour le personnel/admin.
  * Note: les vues sensibles (decorateurs @staff_member_required) étaient déjà présents pour la plupart; j'ai concentré la restriction côté interface pour éviter les actions via l'UI par des utilisateurs non-admin.
- Ajouts:
  * README (ce fichier) expliquant les changements.
- Livraison:
  * Archive ZIP créée: /mnt/data/gestion_entreprise_modified.zip