from .models import Contrat, Vehicule

def stats_globales(request):
    """Ajoute des statistiques globales au contexte de tous les templates."""
    return {
        'total_vehicules': Vehicule.objects.count(),
        'vehicules_disponibles': Vehicule.objects.filter(disponible=True).count(),
        'contrats_actifs': Contrat.objects.filter(statut='actif').count(),
        'contrats_retard': Contrat.objects.filter(statut='en_retard').count(),
    }