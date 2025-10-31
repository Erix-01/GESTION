from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    # Clients
    path('client/', views.liste_clients, name='liste_clients'),
    path('client/ajouter/', views.ajouter_client, name='ajouter_client'),
    path('client/modifier/<int:id>/', views.modifier_client, name='modifier_client'),
    path('client/detail/<int:id>/', views.detail_client, name='detail_client'),
    path('client/supprimer/<int:id>/', views.confirmer_suppression, {'type_objet': 'client'}, name='supprimer_client'),
    
    # Véhicules
    path('vehicules/', views.liste_vehicules, name='liste_vehicules'),
    path('vehicules/ajouter/', views.ajouter_vehicule, name='ajouter_vehicule'),
    path('vehicules/modifier/<int:id>/', views.modifier_vehicule, name='modifier_vehicule'),
    path('vehicules/supprimer/<int:id>/', views.confirmer_suppression, {'type_objet': 'vehicule'}, name='supprimer_vehicule'),
    path('audit/',views.audit_list, name='audit_list'),
    path('admin_dashbord/', views.admin_dashboard, name='admin_dashboard'),
    # Page publique (client)
    path('catalogue/', views.public_catalogue, name='catalogue'),


    # Exports (staff)
    path('export/clients/', views.export_clients_csv, name='export_clients_csv'),
    path('export/vehicules/', views.export_vehicules_csv, name='export_vehicules_csv'),
    path('export/contrats/', views.export_contrats_csv, name='export_contrats_csv'),

    # Stats for admin dashboard
    path('api/stats/contrats-par-mois/', views.stats_contrats_par_mois, name='stats_contrats_par_mois'),
    path('api/stats/occupation-vehicules/', views.stats_occupation_vehicules, name='stats_occupation_vehicules'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/audit-logs/', views.audit_list, name='audit_list'),
    
    # Contrats
    path('contrats/', views.liste_contrats, name='liste_contrats'),
    path('contrats/creer/', views.creer_contrat, name='creer_contrat'),
    path('contrats/<int:id>/retour/', views.retour_contrat, name='retour_contrat'),
    path('contrats/<int:id>/rupture/', views.rupture_contrat, name='rupture_contrat'),
    path('contrats/supprimer/<int:id>/', views.confirmer_suppression, {'type_objet': 'contrat'}, name='supprimer_contrat'),
    path('contrats/<int:id>/', views.detail_contrat, name='detail_contrat'),
    path('contrats/<int:id>/pdf/', views.contrat_pdf, name='contrat_pdf'),
    
    # API
    path('api/calculer-prix/', views.calculer_prix, name='calculer_prix'),
]
