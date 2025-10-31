from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Client, Vehicule, Contrat
from django.contrib.auth.models import User


class GestionAdminSite(AdminSite):
    site_header = 'ACA Location - Administration'
    site_title = 'ACA Admin'
    index_title = 'Tableau de bord'
    index_template = 'admin/index.html'

    def get_stats_context(self, request):
        # Statistiques de base
        stats = {
            'total_clients': Client.objects.count(),
            'total_vehicules': Vehicule.objects.count(),
            'vehicules_disponibles': Vehicule.objects.filter(disponible=True).count(),
            'contrats_actifs': Contrat.objects.filter(statut='actif').count(),
            'contrats_retard': Contrat.objects.filter(statut='en_retard').count(),
        }
        
        # Tendances mensuelles
        six_months_ago = datetime.now() - timedelta(days=180)
        contrats_par_mois = (Contrat.objects
            .filter(date_creation__gte=six_months_ago)
            .annotate(mois=TruncMonth('date_creation'))
            .values('mois')
            .annotate(total=Count('id'))
            .order_by('mois'))

        revenus_par_mois = (Contrat.objects
            .filter(date_creation__gte=six_months_ago)
            .annotate(mois=TruncMonth('date_creation'))
            .values('mois')
            .annotate(total=Sum('montant_total'))
            .order_by('mois'))

        # Top véhicules
        top_vehicules = (Vehicule.objects
            .annotate(nombre_contrats=Count('contrat'))
            .order_by('-nombre_contrats')[:5])

        return {
            'stats': stats,
            'contrats_par_mois': list(contrats_par_mois),
            'revenus_par_mois': list(revenus_par_mois),
            'top_vehicules': top_vehicules,
            'contrats_recent': Contrat.objects.all().order_by('-date_creation')[:5],
            'vehicules_disponibles': Vehicule.objects.filter(disponible=True).order_by('prix_journalier')[:5],
            'total_users': User.objects.count(),
        }

    def index(self, request, extra_context=None):
        """Affiche le dashboard personnalisé avec stats."""
        context = self.get_stats_context(request)
        if extra_context:
            context.update(extra_context)
        return super().index(request, context)

    def get_urls(self):
        """Ajouter une route /admin/dashboard/ pointant vers l'index personnalisé."""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.index), name='dashboard'),
        ]
        return custom_urls + urls


# Créer l'instance du site admin personnalisé
custom_admin_site = GestionAdminSite(name='admin')


class ClientAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'telephone', 'email', 'date_creation']
    search_fields = ['nom', 'prenom', 'telephone']
    list_filter = ['date_creation']
    list_per_page = 20
    date_hierarchy = 'date_creation'


class VehiculeAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'marque', 'modele', 'annee', 'immatriculation', 'prix_journalier', 'disponibilite_preview']
    list_filter = ['type_vehicule', 'disponible', 'date_ajout']
    search_fields = ['marque', 'modele', 'immatriculation']
    list_per_page = 20
    date_hierarchy = 'date_ajout'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:80px;height:auto;border-radius:4px;" class="image-preview"/>', obj.image.url)
        return "-"
    image_preview.short_description = 'Photo'

    def disponibilite_preview(self, obj):
        if obj.disponible:
            return format_html('<span class="status-tag status-active">Disponible</span>')
        return format_html('<span class="status-tag status-inactive">Indisponible</span>')
    disponibilite_preview.short_description = 'Statut'


class ContratAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'vehicule', 'date_debut', 'date_fin', 'statut_display', 'montant_total', 'action_buttons']
    list_filter = ['statut', 'date_creation', 'mode_paiement']
    search_fields = ['client__nom', 'client__prenom', 'vehicule__marque', 'vehicule__modele']
    readonly_fields = ['date_creation']
    list_per_page = 20
    date_hierarchy = 'date_creation'

    def statut_display(self, obj):
        status_classes = {
            'actif': 'status-active',
            'termine': 'status-inactive',
            'en_retard': 'status-pending',
            'rompu': 'status-inactive'
        }
        return format_html('<span class="status-tag {}">{}</span>',
                          status_classes.get(obj.statut, ''),
                          obj.get_statut_display())
    statut_display.short_description = 'Statut'

    def action_buttons(self, obj):
        parts = []
        # Lien vers la page de détail / PDF public
        try:
            pdf_url = reverse('contrat_pdf', args=[obj.pk])
            parts.append(f'<a class="button" href="{pdf_url}" target="_blank">PDF</a>')
        except Exception:
            pass

        # Lien vers la rupture via l'admin (route ajoutée plus bas)
        if obj.statut == 'actif':
            try:
                rompre_url = reverse('admin:rompre_contrat', args=[obj.pk])
                parts.append(f'<a class="button" style="margin-left:6px;background:#e74c3c;" href="{rompre_url}">Rompre</a>')
            except Exception:
                pass

        return format_html(' '.join(parts)) if parts else '-'
    action_buttons.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:contrat_id>/rompre/', 
                self.admin_site.admin_view(self.rompre_contrat), 
                name='rompre_contrat'),
        ]
        return custom_urls + urls

    def rompre_contrat(self, request, contrat_id):
        contrat = get_object_or_404(Contrat, id=contrat_id)
        if request.method == 'POST':
            # Marquer comme rompu et libérer véhicule
            contrat.statut = 'rompu'
            contrat.save()
            contrat.vehicule.disponible = True
            contrat.vehicule.save()
            self.message_user(request, 'Le contrat a été rompu avec succès.')
            return redirect('..')

        context = {
            'title': f'Rompre le contrat {contrat}',
            'contrat': contrat,
            'opts': self.model._meta,
        }
        return render(request, 'admin/contrat/rompre_contrat.html', context)


# Enregistrer les modèles sur le site admin personnalisé
custom_admin_site.register(Client, ClientAdmin)
custom_admin_site.register(Vehicule, VehiculeAdmin)
custom_admin_site.register(Contrat, ContratAdmin)

# Enregistrer la gestion des utilisateurs et groupes pour l'admin personnalisé
try:
    custom_admin_site.register(User, UserAdmin)
    custom_admin_site.register(Group, GroupAdmin)
except Exception:
    # Si pour une raison quelconque l'enregistrement échoue (environnements de test spéciaux),
    # on ignore pour ne pas casser l'admin principal.
    pass
