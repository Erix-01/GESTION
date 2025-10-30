from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta
from django.urls import reverse
from .models import Client, Vehicule, Contrat
from .forms import ClientForm, VehiculeForm, ContratForm

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
    return render(request, 'gestion/clients/liste.html', {'clients': clients})

def ajouter_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client ajouté avec succès!')
            return redirect('liste_clients')
    else:
        form = ClientForm()
    return render(request, 'gestion/clients/ajouter.html', {'form': form})

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
    return render(request, 'gestion/clients/modifier.html', {'form': form, 'client': client})

def detail_client(request, id):
    client = get_object_or_404(Client, id=id)
    contrats = client.historique_contrats()
    return render(request, 'gestion/clients/details.html', {'client': client, 'contrats': contrats})

# Vues pour les véhicules
def liste_vehicules(request):
    vehicules = Vehicule.objects.all()
    return render(request, 'gestion/vehicules/liste.html', {'vehicules': vehicules})

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
    statut_filtre = request.GET.get('statut')
    if statut_filtre:
        contrats = Contrat.objects.filter(statut=statut_filtre)
    else:
        contrats = Contrat.objects.all()
    return render(request, 'gestion/contrats/liste.html', {'contrats': contrats, 'statut_filtre': statut_filtre})

def creer_contrat(request):
    if request.method == 'POST':
        form = ContratForm(request.POST)
        if form.is_valid():
            contrat = form.save()
            messages.success(request, 'Contrat créé avec succès!')
            return redirect('liste_contrats')
    else:
        form = ContratForm()
    return render(request, 'gestion/contrats/creer.html', {'form': form})

def retour_contrat(request, id):
    contrat = get_object_or_404(Contrat, id=id)
    if request.method == 'POST':
        contrat.statut = 'termine'
        contrat.date_retour = timezone.now()
        contrat.vehicule.disponible = True
        contrat.vehicule.save()
        contrat.save()
        messages.success(request, 'Retour du véhicule enregistré avec succès!')
        return redirect('liste_contrats')
    return render(request, 'gestion/contrats/retour.html', {'contrat': contrat})

def rupture_contrat(request, id):
    contrat = get_object_or_404(Contrat, id=id)
    if request.method == 'POST':
        contrat.statut = 'rompu'
        contrat.date_rupture = timezone.now()
        contrat.vehicule.disponible = True
        contrat.vehicule.save()
        contrat.save()
        messages.success(request, 'Rupture de contrat enregistrée avec succès!')
        return redirect('liste_contrats')
    return render(request, 'gestion/contrats/rupture.html', {'contrat': contrat})

def confirmer_suppression(request, id, type_objet):
    if type_objet == 'client':
        obj = get_object_or_404(Client, id=id)
        redirect_url = 'liste_clients'
        label = f"{obj.prenom} {obj.nom}"
    elif type_objet == 'vehicule':
        obj = get_object_or_404(Vehicule, id=id)
        redirect_url = 'liste_vehicules'
        label = f"{obj.marque} {obj.modele}"
    elif type_objet == 'contrat':
        obj = get_object_or_404(Contrat, id=id)
        redirect_url = 'liste_contrats'
        label = f"Contrat #{obj.id}"
    else:
        raise Http404("Type d'objet non valide")

    if request.method == 'POST':
        obj.delete()
        messages.success(request, f'{type_objet.capitalize()} supprimé avec succès!')
        return redirect(redirect_url)

    return render(request, 'gestion/confirm_delete.html', {
        'label': label,
        'type_objet': type_objet
    })