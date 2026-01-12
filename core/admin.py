from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.utils.html import format_html
from .models import Utilisateur, Service, Demande, Paiement

@admin.register(Utilisateur)
class UtilisateurAdmin(BaseUserAdmin):
    list_display = ('username', 'matricule', 'email','nom','prenom', 'telephone', '_avatar','date_naissance', 'date_creation')
    readonly_fields = ('matricule', '_avatar', 'date_creation')
    search_fields = ('username', 'matricule', 'email', 'telephone')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('matricule', 'telephone', 'nom', 'prenom', 'avatar', 'date_naissance', 'date_creation')}),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            return super().get_form(request, obj, **kwargs)
        return super().get_form(request, obj, **kwargs)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id','titre', 'prix','devise', 'actif', 'created_at', 'updated_at')
    list_filter = ('actif',)
    search_fields = ('titre',)

@admin.register(Demande)
class DemandeAdmin(admin.ModelAdmin):
    list_display = ('id','utilisateur', 'service', 'statut', 'date','latitude', 'longitude', 'afficher_carte')
    list_filter = ('statut',)
    search_fields = ('utilisateur__username', 'service__titre')
    readonly_fields = ('id', 'date', 'carte_leaflet')
    fieldsets = (
        ('Informations', {
            'fields': ('id', 'utilisateur', 'service', 'date')
        }),
        ('Localisation', {
            'fields': ('latitude', 'longitude', 'carte_leaflet')
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
    )
    
    def carte_leaflet(self, obj):
        """Display Leaflet map for the demand location"""
        if not obj.latitude or not obj.longitude:
            return format_html("<p style='color: red;'>Localisation non disponible</p>")
        
        map_html = f"""
        <div id="map" style="width: 100%; height: 400px; border: 2px solid #27ae60; margin-top: 10px;"></div>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
        <script>
            (function() {{
                const map = L.map('map').setView([{obj.latitude}, {obj.longitude}], 15);
                
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OpenStreetMap contributors',
                    maxZoom: 19
                }}).addTo(map);
                
                const marker = L.marker([{obj.latitude}, {obj.longitude}]).addTo(map);
                marker.bindPopup(`
                    <div style="text-align: center;">
                        <strong>Demande #GTAP-{obj.id:06d}</strong><br>
                        Service: {obj.service.titre}<br>
                        Utilisateur: {obj.utilisateur.username}<br>
                        <small>Statut: {obj.statut}</small>
                    </div>
                `);
                
                // Custom marker icon - green
                const greenIcon = L.icon({{
                    iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2327ae60" width="32" height="32"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2m0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3m0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg>',
                    iconSize: [32, 32],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32]
                }});
                
                marker.setIcon(greenIcon);
            }})();
        </script>
        """
        return format_html(map_html)
    
    carte_leaflet.short_description = "Carte de Localisation"
    
    def afficher_carte(self, obj):
        """Link to view map in changelist"""
        if obj.latitude and obj.longitude:
            return format_html('<a href="https://maps.google.com/?q={},{}" target="_blank" style="color: #27ae60; text-decoration: none;">Localiser le lieu</a>', obj.latitude, obj.longitude)
        return "N/A"
    afficher_carte.short_description = "Carte"

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('demande', 'montant', 'methode', 'statut', 'transaction_id', 'paye_le', 'created_at')
    list_filter = ('statut', 'methode')
    search_fields = ('demande__utilisateur__username', 'transaction_id')





