from datetime import date
import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.safestring import mark_safe

from gtaplitserver import settings


class Utilisateur(AbstractUser):
    matricule = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        editable=False
    )
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    nom = models.CharField(max_length=100, blank=True, null=True)
    prenom = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(
        upload_to='avatars/%Y/',
        verbose_name="Photo Profil",
        null=True,
        blank=True
    )
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    date_creation = models.DateTimeField(default=timezone.now, verbose_name="Date de création")

    def _avatar(self):
        if self.avatar:
            return mark_safe(
                f'<div style="width: 50px; height: 50px; padding:3px; border: 1px solid #B5C0D0; '
                f'border-radius: 10px; background-image: url({self.avatar.url}); '
                f'background-size: cover; background-repeat: no-repeat;"></div>'
            )
        return '(aucune image)'
    _avatar.short_description = 'Avatar'

    def __str__(self):
        return self.get_full_name() or self.username

    def save(self, *args, **kwargs):
        if not self.matricule:
            self.matricule = self.generate_unique_matricule()
        super().save(*args, **kwargs)

    def generate_unique_matricule(self):
        while True:
            code = "GTAP" + ''.join(random.choices(string.digits, k=5))
            if not Utilisateur.objects.filter(matricule=code).exists():
                return code


class Service(models.Model):
    DEVICES_CHOICES = [
        ('USD', 'Dollar américain'),
        ('CDF', 'Franc congolais'),
        ('EUR', 'Euro'),
    ]

    titre = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(
        max_length=3,
        choices=DEVICES_CHOICES,
        default='CDF',  # valeur par défaut
    )
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.titre} ({self.prix} {self.devise})"


class Demande(models.Model):
    STATUTS = [
        ("EN_ATTENTE", "En attente"),
        ("ACCEPTEE", "Acceptée"),
        ("REFUSEE", "Refusée"),
    ]
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="demandes")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="demandes")
    date = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=10, choices=STATUTS, default="EN_ATTENTE")   
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    def __str__(self):
        return f"Demande#{self.pk} - {self.utilisateur} - {self.service.titre}"


class Paiement(models.Model):
    METHODES = [
        ("MOBILE_MONEY", "Mobile Money"),
        ("CARTE", "Carte bancaire"),
        ("ESPECES", "Espèces"),
    ]
    STATUTS = [
        ("EN_ATTENTE", "En attente"),
        ("SUCCES", "Succès"),
        ("ECHEC", "Échec"),
    ]

    demande = models.OneToOneField(Demande, on_delete=models.CASCADE, related_name="paiement")
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    methode = models.CharField(max_length=20, choices=METHODES)
    statut = models.CharField(max_length=10, choices=STATUTS, default="EN_ATTENTE")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    paye_le = models.DateTimeField(blank=True, null=True,auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement Demande#{self.demande.pk} - {self.statut}"
