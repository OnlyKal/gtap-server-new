from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
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
    list_display = ('id','utilisateur', 'service', 'statut', 'date','latitude', 'longitude')
    list_filter = ('statut',)
    search_fields = ('utilisateur__username', 'service__titre')

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('demande', 'montant', 'methode', 'statut', 'transaction_id', 'paye_le', 'created_at')
    list_filter = ('statut', 'methode')
    search_fields = ('demande__utilisateur__username', 'transaction_id')





