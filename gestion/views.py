from django.shortcuts import render, redirect, get_object_or_404
from django.http.response import HttpResponseRedirect
from django.http import JsonResponse, Http404, HttpResponse
import csv
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta, datetime
from django.urls import reverse
from .models import Client, Vehicule, Contrat
from .forms import ClientForm, VehiculeForm, ContratForm
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from django.http import FileResponse
import io

@staff_member_required
def admin_dashboard(request):
    return render(request, 'gestion/admin_dashboard.html')

@staff_member_required
def export_clients_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="clients.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Nom', 'Prénom', 'Email', 'Téléphone'])
    
    clients = Client.objects.all()
    for client in clients:
        writer.writerow([client.nom, client.prenom, client.email, client.telephone])
    
    return response

@staff_member_required
def export_vehicules_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="vehicules.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Marque', 'Modèle', 'Année', 'Kilométrage', 'Prix journalier', 'Disponible'])
    
    vehicules = Vehicule.objects.all()
    for vehicule in vehicules:
        writer.writerow([vehicule.marque, vehicule.modele, vehicule.annee, vehicule.kilometrage, vehicule.prix_journalier, vehicule.disponible])
    
    return response


@staff_member_required
def export_clients_en_retard_csv(request):
    """Export CSV des clients ayant des contrats en retard."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="clients_en_retard.csv"'

    writer = csv.writer(response)
    writer.writerow(['Nom', 'Prénom', 'Email', 'Téléphone', 'Contrat ID', 'Véhicule', 'Date fin prévue', 'Jours de retard'])

    today = timezone.now().date()
    contrats_retard = Contrat.objects.filter(statut='en_retard')
    for contrat in contrats_retard:
        jours_retard = (today - contrat.date_fin).days if contrat.date_fin else ''
        client = contrat.client
        writer.writerow([client.nom, client.prenom, client.email, client.telephone, contrat.id, f"{contrat.vehicule.marque} {contrat.vehicule.modele}", contrat.date_fin, jours_retard])

    return response


@staff_member_required
def export_vehicules_loues_csv(request):
    """Export CSV des véhicules actuellement loués (contrats actifs)."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="vehicules_loues.csv"'

    writer = csv.writer(response)
    writer.writerow(['Véhicule', 'Immatriculation', 'Client', 'Date début', 'Date fin prévue', 'Contrat ID'])

    contrats_actifs = Contrat.objects.filter(statut='actif')
    for contrat in contrats_actifs:
        vehicule = contrat.vehicule
        client = contrat.client
        writer.writerow([f"{vehicule.marque} {vehicule.modele}", vehicule.immatriculation, f"{client.nom} {client.prenom}", contrat.date_debut, contrat.date_fin, contrat.id])

    return response


@staff_member_required
def clients_en_retard(request):
    """Affiche une page listant les clients avec contrats en retard."""
    contrats_retard = Contrat.objects.filter(statut='en_retard').select_related('client', 'vehicule')

    rows = []
    today = timezone.now().date()
    for c in contrats_retard:
        jours = (today - c.date_fin).days if c.date_fin else None
        rows.append({'contrat': c, 'jours_retard': jours})

    # Paginate the rows
    page = request.GET.get('page', 1)
    paginator = Paginator(rows, 25)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)

    return render(request, 'gestion/clients/en_retard.html', {
        'rows': page_obj,
        'today': today,
    })

@staff_member_required
@staff_member_required
def audit_list(request):
    # Get the list of audits and paginate
    audits = []
    page = request.GET.get('page', 1)
    paginator = Paginator(audits, 25)  # 25 audits per page
    
    try:
        audits_page = paginator.page(page)
    except:
        audits_page = paginator.page(1)
    
    return render(request, 'gestion/audit_list.html', {
        'audits': audits_page
    })

def export_contrats_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contrats.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Client', 'Véhicule', 'Date début', 'Date fin prévue', 'Date retour', 'Statut', 'Montant total'])
    
    contrats = Contrat.objects.all()
    for contrat in contrats:
        writer.writerow([
            f"{contrat.client.nom} {contrat.client.prenom}",
            f"{contrat.vehicule.marque} {contrat.vehicule.modele}",
            contrat.date_debut,
            contrat.date_fin_prevue,
            contrat.date_retour,
            contrat.statut,
            contrat.montant_total
        ])
    
    return response

@staff_member_required
def stats_contrats_par_mois(request):
    # Calculer les contrats par mois pour les 12 derniers mois
    douze_mois = timezone.now() - timedelta(days=365)
    contrats_par_mois = (
        Contrat.objects
        .filter(date_creation__gte=douze_mois)
        .annotate(mois=TruncMonth('date_creation'))
        .values('mois')
        .annotate(total=Count('id'))
        .order_by('mois')
    )
    
    # Formater les données pour le graphique
    labels = []
    data = []
    for stat in contrats_par_mois:
        labels.append(stat['mois'].strftime('%B %Y'))
        data.append(stat['total'])
        
    return JsonResponse({
        'labels': labels,
        'data': data
    })

@staff_member_required
def stats_occupation_vehicules(request):
    vehicules = Vehicule.objects.all()
    data = []
    
    for vehicule in vehicules:
        # Calculer le nombre de jours loués sur les 30 derniers jours
        trente_jours = timezone.now().date() - timedelta(days=30)
        jours_loues = (
            Contrat.objects
            .filter(vehicule=vehicule)
            .filter(date_debut__gte=trente_jours)
            .count()
        )
        
        taux_occupation = (jours_loues / 30) * 100 if jours_loues > 0 else 0
        
        data.append({
            'vehicule': f"{vehicule.marque} {vehicule.modele}",
            'taux_occupation': round(taux_occupation, 2)
        })
    
    return JsonResponse({'data': data})

def index(request):
    stats = {
        'total_clients': Client.objects.count(),
        'total_vehicules': Vehicule.objects.count(),
        'vehicules_disponibles': Vehicule.objects.filter(disponible=True).count(),
        'contrats_actifs': Contrat.objects.filter(statut='actif').count(),
        'contrats_retard': Contrat.objects.filter(statut='en_retard').count(),
    }
    
    contrats_recent = Contrat.objects.all().order_by('-date_creation')[:5]
    vehicules_disponibles = Vehicule.objects.filter(disponible=True)[:5]
    
    # Envoyer les rappels automatiques
    contrats_pour_rappel = Contrat.objects.filter(statut='actif')
    rappels = []
    for contrat in contrats_pour_rappel:
        rappel = contrat.envoyer_rappel()
        if rappel:
            rappels.append(rappel)
    
    context = {
        'stats': stats,
        'contrats_recent': contrats_recent,
        'vehicules_disponibles': vehicules_disponibles,
        'rappels': rappels,
    }
    return render(request, 'gestion/index.html', context)

# Vues pour les clients
def liste_clients(request):
    clients = Client.objects.all().order_by('nom')
    return render(request, 'gestion/client/liste.html', {'clients': clients})

@staff_member_required
def ajouter_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client ajouté avec succès!')
            return redirect('liste_clients')
    else:
        form = ClientForm()
    return render(request, 'gestion/client/ajouter.html', {'form': form})

@staff_member_required
def modifier_client(request, id):
    client = get_object_or_404(Client, id=id)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client modifié avec succès!')
            return redirect('liste_clients')
    else:
        form = ClientForm(instance=client)
    return render(request, 'gestion/client/modifier.html', {'form': form, 'client': client})

def detail_client(request, id):
    client = get_object_or_404(Client, id=id)
    contrats = client.historique_contrats()
    return render(request, 'gestion/client/details.html', {'client': client, 'contrats': contrats})

# Vues pour les véhicules
def liste_vehicules(request):
    vehicules = Vehicule.objects.all().order_by('marque')
    return render(request, 'gestion/vehicules/liste.html', {'vehicules': vehicules})

def public_catalogue(request):
    """Vue publique: catalogue client avec images et caractéristiques."""
    vehicules = Vehicule.objects.filter(disponible=True).order_by('-date_ajout')
    return render(request, 'gestion/public/catalogue.html', {'vehicules': vehicules})

@staff_member_required
def ajouter_vehicule(request):
    if request.method == 'POST':
        form = VehiculeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Véhicule ajouté avec succès!')
            return redirect('liste_vehicules')
    else:
        form = VehiculeForm()
    return render(request, 'gestion/vehicules/ajouter.html', {'form': form})

@staff_member_required
def modifier_vehicule(request, id):
    vehicule = get_object_or_404(Vehicule, id=id)
    if request.method == 'POST':
        form = VehiculeForm(request.POST, instance=vehicule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Véhicule modifié avec succès!')
            return redirect('liste_vehicules')
    else:
        form = VehiculeForm(instance=vehicule)
    return render(request, 'gestion/vehicules/modifier.html', {'form': form, 'vehicule': vehicule})

# Vues pour les contrats
def liste_contrats(request):
    statut = request.GET.get('statut')
    if statut:
        contrats = Contrat.objects.filter(statut=statut).order_by('-date_creation')
    else:
        contrats = Contrat.objects.all().order_by('-date_creation')
    return render(request, 'gestion/contrats/liste.html', {'contrats': contrats, 'statut_filtre': statut})

@staff_member_required
def creer_contrat(request):
    if request.method == 'POST':
        form = ContratForm(request.POST)
        if form.is_valid():
            try:
                contrat = form.save(commit=False)

                # Calculer la date de fin
                contrat.date_fin = contrat.date_debut + timedelta(days=contrat.nb_jours)

                # Calculer le montant total
                vehicule = form.cleaned_data['vehicule']
                nb_jours = form.cleaned_data['nb_jours']
                contrat.montant_total = vehicule.calculer_prix_location(nb_jours)

                # Gérer les détails de paiement
                details_paiement = {}
                mode_paiement = form.cleaned_data['mode_paiement']

                if mode_paiement == 'carte' and all(k in form.cleaned_data for k in ['numero_carte', 'date_expiration']):
                    details_paiement = {
                        'numero_carte': form.cleaned_data['numero_carte'],
                        'date_expiration': form.cleaned_data['date_expiration']
                    }
                elif mode_paiement == 'virement' and 'rib' in form.cleaned_data:
                    details_paiement = {
                        'rib': form.cleaned_data['rib']
                    }
                elif mode_paiement == 'cheque' and 'numero_cheque' in form.cleaned_data:
                    details_paiement = {
                        'numero_cheque': form.cleaned_data['numero_cheque']
                    }
                elif mode_paiement == 'mobile' and 'numero_telephone' in form.cleaned_data:
                    details_paiement = {
                        'numero_telephone': form.cleaned_data['numero_telephone']
                    }

                contrat.details_paiement = details_paiement

                # Marquer le véhicule comme indisponible
                vehicule.disponible = False
                vehicule.save()

                # Sauvegarder le contrat
                contrat.save()

                messages.success(request, 'Contrat créé avec succès!')
                return redirect('liste_contrats')
            except Exception as e:
                messages.error(request, f'Erreur lors de la création du contrat : {str(e)}')
                return render(request, 'gestion/contrats/creer.html', {'form': form})
    else:
        form = ContratForm()
    
    return render(request, 'gestion/contrats/creer.html', {'form': form})

@staff_member_required
def retour_contrat(request, id):
    contrat = get_object_or_404(Contrat, id=id)
    today = timezone.now().date()
    
    if request.method == 'POST':
        date_retour = timezone.now().date()
        
        # Calculer les pénalités si retard
        if hasattr(contrat, 'est_en_retard') and contrat.est_en_retard():
            if hasattr(contrat, 'calculer_penalites'):
                penalites = contrat.calculer_penalites()
                messages.warning(request, f'Pénalités de retard : {penalites} FCFA')
        
        # Calculer remboursement si retour anticipé
        elif date_retour < contrat.date_fin:
            if hasattr(contrat, 'calculer_remboursement'):
                remboursement = contrat.calculer_remboursement(date_retour)
                if remboursement > 0:
                    messages.info(request, f'Remboursement pour retour anticipé : {remboursement} FCFA')
        
        # Marquer le véhicule comme disponible
        vehicule = contrat.vehicule
        vehicule.disponible = True
        vehicule.save()
        
        # Marquer le contrat comme terminé
        contrat.statut = 'termine'
        contrat.save()
        
        messages.success(request, f'Véhicule {vehicule} retourné avec succès!')
        return redirect('liste_contrats')
    
    return render(request, 'gestion/contrats/retour.html', {
        'contrat': contrat,
        'today': today
    })

@staff_member_required
def rupture_contrat(request, id):
    contrat = get_object_or_404(Contrat, id=id)

    if request.method == 'POST':
        date_rupture = request.POST.get('date_rupture')
        motif_rupture = request.POST.get('motif_rupture')
        frais_rupture = request.POST.get('frais_rupture')

        if date_rupture and motif_rupture and frais_rupture:
            contrat.date_rupture = date_rupture
            contrat.motif_rupture = motif_rupture
            contrat.frais_rupture = frais_rupture
            contrat.statut = 'rompu'
            contrat.save()

            # Libérer le véhicule
            contrat.vehicule.disponible = True
            contrat.vehicule.save()

            messages.success(request, 'Le contrat a été rompu avec succès.')
            return redirect('liste_contrats')
        else:
            messages.error(request, 'Veuillez remplir tous les champs.')

    context = {
        'contrat': contrat
    }
    return render(request, 'gestion/contrats/rupture.html', context)

def detail_contrat(request, id):
    contrat = get_object_or_404(Contrat, id=id)
    # Calculer jours restants si applicable
    jours_restants = None
    if contrat.date_fin:
        jours_restants = (contrat.date_fin - timezone.now().date()).days
    context = {
        'contrat': contrat,
        'jours_restants': jours_restants,
    }
    # Afficher une page de détails dédiée (non le formulaire de retour)
    return render(request, 'gestion/contrats/detail.html', context)


@staff_member_required
def contrat_pdf(request, id):
    """Génère un PDF simple du contrat et renvoie en téléchargement."""
    contrat = get_object_or_404(Contrat, id=id)

    # Génération PDF avec reportlab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception:
        return HttpResponse('La génération PDF nécessite la bibliothèque reportlab.', status=500)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # En-tête
    c.setFont('Helvetica-Bold', 16)
    c.drawString(40, height - 60, f'Contrat #{contrat.id} - ACA Location')

    c.setFont('Helvetica', 12)
    y = height - 100
    lignes = [
        f'Client: {contrat.client}',
        f'Vehicule: {contrat.vehicule}',
        f'Date de création: {contrat.date_creation.strftime("%d/%m/%Y %H:%M") if contrat.date_creation else "-"}',
        f'Date début: {contrat.date_debut}',
        f'Date fin: {contrat.date_fin}',
        f'Nombre de jours: {contrat.nb_jours}',
    f'Montant total: {contrat.montant_total} FCFA',
        f'Statut: {contrat.get_statut_display()}',
    ]

    for ligne in lignes:
        c.drawString(40, y, ligne)
        y -= 20
        if y < 80:
            c.showPage()
            y = height - 60

    c.showPage()
    c.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'contrat_{contrat.id}.pdf')


@staff_member_required
def confirmer_suppression(request, type_objet, id):
    """Vue générique pour confirmer suppression d'un objet (client, vehicule, contrat)."""
    obj = None
    label = ''
    if type_objet == 'client':
        obj = get_object_or_404(Client, id=id)
        label = str(obj)
    elif type_objet == 'vehicule':
        obj = get_object_or_404(Vehicule, id=id)
        label = str(obj)
    elif type_objet == 'contrat':
        obj = get_object_or_404(Contrat, id=id)
        label = str(obj)
    else:
        messages.error(request, 'Type d\'objet inconnu.')
        return redirect('index')

    if request.method == 'POST':
        # Effectuer la suppression
        obj.delete()
        messages.success(request, f'{type_objet.capitalize()} supprimé(e) avec succès.')
        # Redirection logique
        if type_objet == 'client':
            return redirect('liste_clients')
        if type_objet == 'vehicule':
            return redirect('liste_vehicules')
        return redirect('liste_contrats')

    return render(request, 'gestion/confirm_delete.html', {'type': type_objet, 'label': label, 'id': id})
def calculer_prix(request):
    if request.method == 'GET' and 'vehicule_id' in request.GET and 'nb_jours' in request.GET:
        try:
            vehicule = Vehicule.objects.get(id=request.GET['vehicule_id'])
            nb_jours = int(request.GET['nb_jours'])
            prix = vehicule.calculer_prix_location(nb_jours)
            return JsonResponse({'prix': prix})
        except (Vehicule.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Données invalides'})
    return JsonResponse({'error': 'Requête invalide'})