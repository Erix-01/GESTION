from django.db import models
from django.core.validators import MinValueValidator
from datetime import date, timedelta
import json
from django.utils import timezone

class Client(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
    def contrats_actifs(self):
        return self.contrat_set.filter(statut='actif')
    
    def historique_contrats(self):
        return self.contrat_set.all().order_by('-date_creation')
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"

class Vehicule(models.Model):
    TYPE_VEHICULE = [
        ('voiture', 'Voiture'),
        ('moto', 'Moto'),
    ]
    
    type_vehicule = models.CharField(max_length=20, choices=TYPE_VEHICULE)
    marque = models.CharField(max_length=100)
    modele = models.CharField(max_length=100)
    annee = models.IntegerField()
    immatriculation = models.CharField(max_length=20, unique=True)
    prix_journalier = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cylindree = models.IntegerField(blank=True, null=True)
    nombre_portes = models.IntegerField(blank=True, null=True)
    disponible = models.BooleanField(default=True)
    # Image principale du véhicule (optionnelle)
    image = models.ImageField(upload_to='vehicules/', blank=True, null=True)
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.marque} {self.modele} ({self.immatriculation})"
    
    def calculer_prix_location(self, nb_jours):
        prix_total = float(self.prix_journalier) * nb_jours
        
        # Réductions pour locations longue durée
        if nb_jours > 30:
            prix_total *= 0.7  # 30% de réduction pour plus d'un mois
        elif nb_jours > 14:
            prix_total *= 0.85  # 15% de réduction pour plus de 2 semaines
        elif nb_jours > 7:
            prix_total *= 0.9  # 10% de réduction pour plus d'une semaine
            
        return round(prix_total, 2)
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation JSON."""
        return {
            'id': self.id,
            'type_vehicule': self.type_vehicule,
            'marque': self.marque,
            'modele': self.modele,
            'immatriculation': self.immatriculation,
            'prix_journalier': float(self.prix_journalier),
            'disponible': self.disponible,
            'image': self.image.url if self.image else None,
        }
    
    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ['-date_ajout']

    def calculer_prix_total(self, nb_jours):
        prix_total = self.prix_journalier * nb_jours
        
        if self.type_vehicule == 'voiture' and nb_jours >= 7:
            prix_total *= 0.9  # 10% de réduction
        elif self.type_vehicule == 'moto' and self.cylindree and self.cylindree > 600:
            prix_total *= 1.15  # 15% de surtaxe
        
        return prix_total
            
        return round(prix_total, 2)
    
    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"

class Contrat(models.Model):
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('termine', 'Terminé'),
        ('en_retard', 'En retard'),
        ('rompu', 'Rompu'),
    ]
    
    MODE_PAIEMENT = [
        ('carte', 'Carte bancaire'),
        ('virement', 'Virement'),
        ('especes', 'Espèces'),
        ('cheque', 'Chèque'),
        ('mobile', 'Paiement mobile'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    nb_jours = models.IntegerField(validators=[MinValueValidator(1)])
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT, default='especes')
    details_paiement = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return f"Contrat #{self.id} - {self.client} - {self.vehicule}"
    
    def jours_restants(self):
        aujourdhui = timezone.now().date()
        if aujourdhui > self.date_fin:
            return 0
        return (self.date_fin - aujourdhui).days
    
    def est_en_retard(self):
        return self.date_fin < timezone.now().date() and self.statut == 'actif'
        
    def calculer_penalites(self):
        """Calcule les pénalités en cas de retard."""
        if not self.est_en_retard():
            return 0
        
        jours_retard = (timezone.now().date() - self.date_fin).days
        penalite_journaliere = float(self.vehicule.prix_journalier) * 1.5  # 150% du prix journalier
        return round(jours_retard * penalite_journaliere, 2)
    
    def calculer_remboursement(self, date_retour):
        """Calcule le montant à rembourser en cas de retour anticipé."""
        # Accepter datetime ou date
        if date_retour is None:
            return 0

        if hasattr(date_retour, 'date'):
            date_retour = date_retour.date()

        # Si le retour est à la date de fin ou après : pas de remboursement
        if date_retour >= self.date_fin:
            return 0

        # Si le retour est avant la date de début, considérer remboursement total (politique choisie)
        if date_retour <= self.date_debut:
            # Remboursement total moins frais de dossier (10%)
            montant_total = float(self.montant_total)
            remboursement = montant_total * 0.9
            return round(max(remboursement, 0), 2)

        # Nombre de jours non utilisés (jours entiers après la date de retour)
        jours_non_utilises = (self.date_fin - date_retour).days
        if jours_non_utilises <= 0:
            return 0

        # Calcul du prix journalier basé sur le montant total et nombre de jours
        try:
            montant_journalier = float(self.montant_total) / float(self.nb_jours)
        except Exception:
            # Dégradation gracieuse si données absentes
            montant_journalier = float(self.vehicule.prix_journalier)

        # Politique : rembourser 70% du montant journalier pour chaque jour non utilisé
        TAUX_REMBOURSEMENT = 0.7
        remboursement = montant_journalier * jours_non_utilises * TAUX_REMBOURSEMENT

        # Appliquer éventuellement un frais fixe de traitement (par exemple 5 FCFA)
        frais_traitement = 5.0
        remboursement_net = remboursement - frais_traitement
        if remboursement_net < 0:
            remboursement_net = 0

        return round(remboursement_net, 2)
    
    def sauvegarder_json(self):
        data = {
            'contrat_id': self.id,
            'client': {
                'nom': self.client.nom,
                'prenom': self.client.prenom,
                'telephone': self.client.telephone,
                'email': self.client.email,
            },
            'vehicule': {
                'type': self.vehicule.type_vehicule,
                'marque': self.vehicule.marque,
                'modele': self.vehicule.modele,
                'immatriculation': self.vehicule.immatriculation,
            },
            'dates': {
                'creation': self.date_creation.isoformat(),
                'debut': self.date_debut.isoformat(),
                'fin': self.date_fin.isoformat(),
            },
            'details_location': {
                'nb_jours': self.nb_jours,
                'montant_total': float(self.montant_total),
                'statut': self.statut,
            }
        }
        
        try:
            import os
            os.makedirs('contrats', exist_ok=True)
            with open(f'contrats/contrat_{self.id}.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde JSON: {e}")
    
    def envoyer_rappel(self):
        jours_restants = self.jours_restants()
        if jours_restants <= 2 and jours_restants > 0:
            message = f"Rappel: Votre location du véhicule {self.vehicule} se termine dans {jours_restants} jour(s)."
            print(f"ENVOI RAPPEL À {self.client.telephone}: {message}")
            return message
        return None
    
    def save(self, *args, **kwargs):
        if self.est_en_retard() and self.statut == 'actif':
            self.statut = 'en_retard'
        
        super().save(*args, **kwargs)
        self.sauvegarder_json()
    
    class Meta:
        verbose_name = "Contrat"
        verbose_name_plural = "Contrats"

# Simple audit log to record create/update/delete on key models
from django.db import models as _models
class AuditLog(_models.Model):
    timestamp = _models.DateTimeField(auto_now_add=True)
    actor = _models.CharField(max_length=150, blank=True, null=True)
    model = _models.CharField(max_length=150)
    object_id = _models.CharField(max_length=150)
    action = _models.CharField(max_length=50)  # created/updated/deleted
    changes = _models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
