from django.core.management.base import BaseCommand
from django.utils import timezone
from gestion.models import Contrat
from gestion.tasks import verifier_contrats_expires, nettoyer_anciens_contrats

class Command(BaseCommand):
    help = 'Vérifie les contrats et envoie des notifications'

    def handle(self, *args, **kwargs):
        self.stdout.write('Vérification des contrats...')
        
        # Vérifier les contrats expirés et envoyer notifications
        verifier_contrats_expires()
        
        # Nettoyer les vieux contrats
        nettoyer_anciens_contrats()
        
        self.stdout.write(self.style.SUCCESS('Vérification terminée avec succès'))