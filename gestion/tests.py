from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Client, Vehicule, Contrat
from datetime import date, timedelta
from django.utils import timezone
from decimal import Decimal

class GestionTestCase(TestCase):
    def setUp(self):
        # Créer un superutilisateur pour les tests
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.client = TestClient()
        self.client.login(username='admin', password='admin123')

        # Créer des données de test
        self.test_client = Client.objects.create(
            nom='Dupont',
            prenom='Jean',
            telephone='0123456789',
            email='jean@example.com'
        )

        self.test_vehicule = Vehicule.objects.create(
            type_vehicule='voiture',
            marque='Renault',
            modele='Clio',
            annee=2020,
            immatriculation='AA-123-BB',
            prix_journalier=Decimal('50.00')
        )

    def test_admin_dashboard(self):
        """Test l'accès au tableau de bord admin"""
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_client_crud(self):
        """Test les opérations CRUD sur les clients"""
        # Create
        response = self.client.post(reverse('ajouter_client'), {
            'nom': 'Martin',
            'prenom': 'Pierre',
            'telephone': '0987654321',
            'email': 'pierre@example.com'
        })
        self.assertEqual(response.status_code, 302)  # Redirection après succès
        self.assertTrue(Client.objects.filter(nom='Martin').exists())

        # Read
        client = Client.objects.get(nom='Martin')
        response = self.client.get(reverse('detail_client', args=[client.id]))
        self.assertEqual(response.status_code, 200)

        # Update
        response = self.client.post(reverse('modifier_client', args=[client.id]), {
            'nom': 'Martin',
            'prenom': 'Paul',
            'telephone': '0987654321',
            'email': 'paul@example.com'
        })
        self.assertEqual(response.status_code, 302)
        client.refresh_from_db()
        self.assertEqual(client.prenom, 'Paul')

    def test_contrat_operations(self):
        """Test les opérations sur les contrats"""
        # Créer un contrat
        # Utiliser une date future fixe pour le test
        debut = date(2025, 10, 31)  # Date fixe dans le futur pour éviter les problèmes de timezone
        date_str = debut.strftime('%Y-%m-%d')
        
        # Préparer les données pour le contrat
        post_data = {
            'client': self.test_client.id,
            'vehicule': self.test_vehicule.id,
            'date_debut': date_str,
            'nb_jours': 7,
            'mode_paiement': 'especes'  # Les détails de paiement sont optionnels pour le mode espèces
        }
        
        # Soumettre le formulaire
        response = self.client.post(reverse('creer_contrat'), post_data)

        # Accepter soit la redirection 302 soit la page finale 200 (client de test peut suivre)
        self.assertIn(response.status_code, (200, 302))  # Vérifier la redirection ou page finale
        self.assertEqual(response.url, reverse('liste_contrats'))  # Vérifier l'URL de redirection

        # Vérifier que le contrat a été créé
        contrat = Contrat.objects.first()
        self.assertIsNotNone(contrat)
        self.assertEqual(contrat.client, self.test_client)
        self.assertEqual(contrat.vehicule, self.test_vehicule)
        self.assertEqual(contrat.nb_jours, 7)
        self.assertEqual(contrat.montant_total, self.test_vehicule.calculer_prix_location(7))
        self.assertEqual(contrat.mode_paiement, 'especes')
        self.assertEqual(contrat.date_debut.strftime('%Y-%m-%d'), date_str)
        self.assertEqual(contrat.date_fin.strftime('%Y-%m-%d'), (debut + timedelta(days=7)).strftime('%Y-%m-%d'))

        # Test du PDF
        response = self.client.get(reverse('contrat_pdf', args=[contrat.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        # Test de la rupture de contrat avec une date future
        date_retour = debut + timedelta(days=3)  # 3 jours après le début
        # Utiliser la vue de retour pour marquer le véhicule comme retourné
        response = self.client.post(reverse('retour_contrat', args=[contrat.id]), {
            'date_retour': date_retour.strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, 302)
        contrat.refresh_from_db()
        self.assertEqual(contrat.statut, 'termine')

    def test_remboursement_calculation(self):
        """Test le calcul des remboursements"""
        debut = date.today()
        fin = debut + timedelta(days=10)
        contrat = Contrat.objects.create(
            client=self.test_client,
            vehicule=self.test_vehicule,
            date_debut=debut,
            date_fin=fin,
            nb_jours=10,
            montant_total=Decimal('500.00')  # 10 jours * 50 FCFA (valeur monétaire utilisée en tests)
        )

        # Test remboursement à mi-contrat
        date_retour = debut + timedelta(days=5)
        remboursement = contrat.calculer_remboursement(date_retour)
    # 5 jours non utilisés * 50 FCFA par jour * 70% - 5 FCFA frais = 170 FCFA (exemple de calcul)
        self.assertEqual(remboursement, 170)

    def test_superuser_permissions(self):
        """Test les permissions du superutilisateur"""
        # Test accès à l'admin
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

        # Test accès au dashboard
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

        # Test accès aux exports
        response = self.client.get(reverse('export_clients_csv'))
        self.assertEqual(response.status_code, 200)
