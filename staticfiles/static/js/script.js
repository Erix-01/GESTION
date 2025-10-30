// ===== SCRIPT PRINCIPAL POUR LA GESTION DE LOCATION =====

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des composants
    initCalculPrix();
    initGestionVehicules();
    initNotifications();
    initFormValidation();
    initAnimations();
    initSidebar();
});

// ===== CALCUL AUTOMATIQUE DES PRIX =====
function initCalculPrix() {
    const vehiculeSelect = document.getElementById('id_vehicule');
    const nbJoursInput = document.getElementById('id_nb_jours');
    const montantDiv = document.getElementById('montant-estime');

    if (vehiculeSelect && nbJoursInput && montantDiv) {
        function calculerPrix() {
            const vehiculeId = vehiculeSelect.value;
            const nbJours = parseInt(nbJoursInput.value);

            if (vehiculeId && nbJours && nbJours > 0) {
                // Afficher un indicateur de chargement
                montantDiv.innerHTML = '<div class="spinner-border spinner-border-sm text-primary-custom" role="status"></div> Calcul en cours...';
                
                fetch(`/api/calculer-prix/?vehicule_id=${vehiculeId}&nb_jours=${nbJours}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Erreur réseau');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.prix) {
                            const prixFormate = new Intl.NumberFormat('fr-FR').format(data.prix);
                            montantDiv.innerHTML = `
                                <strong class="text-success" style="font-size: 1.2em;">
                                    <i class="fas fa-money-bill-wave"></i> ${prixFormate} FCFA
                                </strong>
                                <br>
                                <small class="text-muted">Prix total pour ${nbJours} jour(s)</small>
                            `;
                            
                            // Animation de confirmation
                            montantDiv.classList.add('pulse');
                            setTimeout(() => montantDiv.classList.remove('pulse'), 2000);
                        } else {
                            montantDiv.innerHTML = '<em class="text-danger"><i class="fas fa-exclamation-triangle"></i> Erreur de calcul</em>';
                        }
                    })
                    .catch(error => {
                        console.error('Erreur:', error);
                        montantDiv.innerHTML = '<em class="text-danger"><i class="fas fa-exclamation-triangle"></i> Erreur de connexion</em>';
                    });
            } else {
                montantDiv.innerHTML = '<em class="text-muted"><i class="fas fa-info-circle"></i> Sélectionnez un véhicule et le nombre de jours</em>';
            }
        }

        vehiculeSelect.addEventListener('change', calculerPrix);
        nbJoursInput.addEventListener('input', calculerPrix);
        
        // Calcul initial si des valeurs sont déjà présentes
        if (vehiculeSelect.value && nbJoursInput.value) {
            calculerPrix();
        }
    }
}

// ===== GESTION DYNAMIQUE DES VÉHICULES =====
function initGestionVehicules() {
    const typeSelect = document.getElementById('id_type_vehicule');
    const caracteristiquesDiv = document.getElementById('caracteristiques');

    if (typeSelect && caracteristiquesDiv) {
        function updateCaracteristiques() {
            const type = typeSelect.value;
            let html = '';
            
            if (type === 'voiture') {
                html = `
                    <div class="mb-3">
                        <label for="id_nombre_portes" class="form-label">
                            <i class="fas fa-door-closed"></i> Nombre de portes
                        </label>
                        <input type="number" name="nombre_portes" class="form-control" id="id_nombre_portes" 
                               min="2" max="5" value="4" required>
                        <div class="form-text">Généralement entre 3 et 5 portes</div>
                    </div>
                `;
            } else if (type === 'moto') {
                html = `
                    <div class="mb-3">
                        <label for="id_cylindree" class="form-label">
                            <i class="fas fa-tachometer-alt"></i> Cylindrée (cc)
                        </label>
                        <input type="number" name="cylindree" class="form-control" id="id_cylindree" 
                               min="50" max="2000" value="500" required>
                        <div class="form-text">Cylindrée en centimètres cubes</div>
                    </div>
                `;
            } else {
                html = '<div class="alert alert-info">Sélectionnez un type de véhicule pour voir les caractéristiques spécifiques</div>';
            }
            
            // Animation de transition
            caracteristiquesDiv.style.opacity = '0';
            setTimeout(() => {
                caracteristiquesDiv.innerHTML = html;
                caracteristiquesDiv.style.opacity = '1';
            }, 300);
        }
        
        typeSelect.addEventListener('change', updateCaracteristiques);
        updateCaracteristiques(); // Initial call
    }
}

// ===== GESTION DES NOTIFICATIONS =====
function initNotifications() {
    // Auto-dismiss des alertes après 5 secondes
    const autoDismissAlerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    autoDismissAlerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.opacity = '0';
                alert.style.transition = 'opacity 0.5s ease';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 500);
            }
        }, 5000);
    });

    // Notification sonore pour les rappels importants
    const rappels = document.querySelectorAll('.alert-warning');
    if (rappels.length > 0) {
        // Simuler une notification (dans un vrai projet, on utiliserait l'API Web Notifications)
        console.log('📢 Rappels importants nécessitent votre attention !');
    }
}

// ===== VALIDATION DES FORMULAIRES =====
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    highlightField(field, false);
                } else {
                    highlightField(field, true);
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showToast('Veuillez remplir tous les champs obligatoires', 'warning');
            }
        });
    });

    // Highlight des champs
    function highlightField(field, isValid) {
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
        }
    }
}

// ===== ANIMATIONS ET EFFETS VISUELS =====
function initAnimations() {
    // Animation d'apparition des éléments
    const animatedElements = document.querySelectorAll('.card, .stat-card, .table');
    
    animatedElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Effet de hover sur les cartes
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// ===== GESTION DE LA SIDEBAR =====
function initSidebar() {
    // Highlight de l'élément actif dans la sidebar
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (currentPath === linkPath || currentPath.startsWith(linkPath + '/')) {
            link.classList.add('active');
        }
        
        // Animation au clic
        link.addEventListener('click', function() {
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Sidebar responsive
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    function handleResize() {
        if (window.innerWidth < 768) {
            sidebar.style.position = 'relative';
            mainContent.style.marginLeft = '0';
        } else {
            sidebar.style.position = 'fixed';
            mainContent.style.marginLeft = '250px';
        }
    }
    
    window.addEventListener('resize', handleResize);
    handleResize(); // Appel initial
}

// ===== FONCTIONS UTILITAIRES =====
function showToast(message, type = 'info') {
    // Créer un toast Bootstrap (simplifié)
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    `;
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove après 5 secondes
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

// ===== GESTION DES CONTRATS =====
function confirmerRetour(contratId) {
    if (confirm('Êtes-vous sûr de vouloir marquer ce véhicule comme retourné ?')) {
        // Simulation d'une requête AJAX (dans un vrai projet, on utiliserait fetch)
        showToast('Retour du véhicule en cours de traitement...', 'info');
        
        // Redirection vers la page de retour
        window.location.href = `/contrats/retour/${contratId}/`;
    }
}

// ===== RECHERCHE ET FILTRES =====
function initRecherche() {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('table tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

// ===== GESTION DES STATISTIQUES =====
function actualiserStats() {
    // Cette fonction pourrait être utilisée pour actualiser les stats en temps réel
    console.log('Actualisation des statistiques...');
    
    // Dans un vrai projet, on ferait une requête AJAX
    // fetch('/api/stats/').then(...)
}

// ===== GESTION DES DATES =====
function formaterDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        weekday: 'long'
    };
    return new Date(dateString).toLocaleDateString('fr-FR', options);
}

// ===== EXPORT DES DONNÉES =====
function exporterDonnees(format = 'json') {
    if (format === 'json') {
        // Simulation d'export JSON
        showToast('Export JSON en cours de préparation...', 'info');
    } else if (format === 'csv') {
        showToast('Export CSV en cours de préparation...', 'info');
    }
}

// ===== GESTION DES ERREURS GLOBALES =====
window.addEventListener('error', function(e) {
    console.error('Erreur globale:', e.error);
    showToast('Une erreur est survenue. Veuillez réessayer.', 'danger');
});

// ===== INITIALISATION AU CHARGEMENT =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚗 Système de location initialisé avec succès !');
    
    // Afficher un message de bienvenue
    if (!localStorage.getItem('welcomeShown')) {
        setTimeout(() => {
            showToast('Bienvenue dans le système de gestion de location !', 'success');
            localStorage.setItem('welcomeShown', 'true');
        }, 1000);
    }
});