from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Contrat

def verifier_contrats_expires():
    """Vérifie les contrats expirés et envoie des notifications."""
    aujourdhui = timezone.now().date()
    
    # Contrats qui expirent dans 2 jours ou moins
    contrats_proche_expiration = Contrat.objects.filter(
        statut='actif',
        date_fin__range=[aujourdhui, aujourdhui + timezone.timedelta(days=2)]
    )
    
    # Contrats expirés
    contrats_expires = Contrat.objects.filter(
        statut='actif',
        date_fin__lt=aujourdhui
    )
    
    # Envoyer notifications pour contrats proche expiration
    for contrat in contrats_proche_expiration:
        jours_restants = (contrat.date_fin - aujourdhui).days
        if contrat.client.email:
            send_mail(
                f'Rappel: Location se termine dans {jours_restants} jour(s)',
                f"""Bonjour {contrat.client.prenom},
                
                Votre location du véhicule {contrat.vehicule} se termine dans {jours_restants} jour(s).
                Merci de prévoir le retour du véhicule.
                
                Cordialement,
                L'équipe de location""",
                settings.DEFAULT_FROM_EMAIL,
                [contrat.client.email],
                fail_silently=True,
            )
    
    # Marquer les contrats expirés
    for contrat in contrats_expires:
        contrat.statut = 'en_retard'
        contrat.save()
        
        if contrat.client.email:
            send_mail(
                'Location expirée - Action requise',
                f"""Bonjour {contrat.client.prenom},
                
                Votre location du véhicule {contrat.vehicule} est expirée.
                Merci de retourner le véhicule dès que possible.
                
                Cordialement,
                L'équipe de location""",
                settings.DEFAULT_FROM_EMAIL,
                [contrat.client.email],
                fail_silently=True,
            )

def nettoyer_anciens_contrats():
    """Archive les vieux contrats terminés (plus de 6 mois)."""
    date_limite = timezone.now() - timezone.timedelta(days=180)
    Contrat.objects.filter(
        statut='termine',
        date_fin__lt=date_limite
    ).update(archive=True)