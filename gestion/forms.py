from django import forms
from .models import Client, Vehicule, Contrat
from datetime import date, timedelta
from django.utils import timezone

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'prenom', 'telephone', 'email']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class VehiculeForm(forms.ModelForm):
    class Meta:
        model = Vehicule
        fields = ['type_vehicule', 'marque', 'modele', 'annee', 'immatriculation', 
                 'prix_journalier', 'cylindree', 'nombre_portes']
        widgets = {
            'type_vehicule': forms.Select(attrs={'class': 'form-control'}),
            'marque': forms.TextInput(attrs={'class': 'form-control'}),
            'modele': forms.TextInput(attrs={'class': 'form-control'}),
            'annee': forms.NumberInput(attrs={'class': 'form-control'}),
            'immatriculation': forms.TextInput(attrs={'class': 'form-control'}),
            'prix_journalier': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cylindree': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre_portes': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ContratForm(forms.ModelForm):
    # Champs supplémentaires pour les détails de paiement
    numero_carte = forms.CharField(max_length=16, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    date_expiration = forms.CharField(max_length=5, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'MM/YY'}))
    rib = forms.CharField(max_length=24, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    numero_cheque = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    numero_telephone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Contrat
        fields = ['vehicule', 'client', 'date_debut', 'nb_jours', 'mode_paiement']
        widgets = {
            'vehicule': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nb_jours': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_date_debut(self):
        date_debut = self.cleaned_data.get('date_debut')
        if date_debut and not isinstance(date_debut, date):
            date_debut = date.fromisoformat(str(date_debut))
        return date_debut

    def clean_nb_jours(self):
        nb_jours = self.cleaned_data.get('nb_jours')
        if nb_jours is None:
            return nb_jours
        if nb_jours < 1:
            raise forms.ValidationError("La durée minimum de location est de 1 jour")
        if nb_jours > 365:
            raise forms.ValidationError("La durée maximum de location est de 365 jours")
        return nb_jours

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Afficher uniquement les véhicules disponibles
        try:
            self.fields['vehicule'].queryset = Vehicule.objects.filter(disponible=True)
        except Exception:
            # Si le modèle n'est pas encore migré, ignorer l'erreur lors de la découverte
            pass

    def clean(self):
        cleaned_data = super().clean()
        vehicule = cleaned_data.get('vehicule')
        date_debut = cleaned_data.get('date_debut')
        nb_jours = cleaned_data.get('nb_jours')

        # Vérifications basiques
        if vehicule and not getattr(vehicule, 'disponible', True):
            raise forms.ValidationError("Ce véhicule n'est pas disponible.")

        if date_debut and date_debut < date.today():
            raise forms.ValidationError("La date de début ne peut pas être dans le passé.")

        if nb_jours and nb_jours <= 0:
            raise forms.ValidationError("Le nombre de jours doit être positif.")

        # Vérifier les conflits de réservation si toutes les données sont présentes
        if vehicule and date_debut and nb_jours:
            date_fin = date_debut + timedelta(days=nb_jours)
            # Statuts qui bloquent la disponibilité
            statuts_bloquants = ['actif', 'en_retard']
            conflits = Contrat.objects.filter(
                vehicule=vehicule,
                date_debut__lte=date_fin,
                date_fin__gte=date_debut,
                statut__in=statuts_bloquants
            )
            # Si on édite un contrat existant, exclure-le
            if self.instance and self.instance.pk:
                conflits = conflits.exclude(pk=self.instance.pk)
            if conflits.exists():
                raise forms.ValidationError("Ce véhicule est déjà réservé pour cette période")

        return cleaned_data