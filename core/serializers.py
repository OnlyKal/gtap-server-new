from django.forms import ValidationError
from rest_framework import serializers
from .models import Utilisateur, Service, Demande, Paiement
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
# 
class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id', 'username', 'matricule','nom', 'prenom', 'email', 'telephone', 'avatar','date_naissance', 'date_creation']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'telephone', 'password']

    def create(self, validated_data):
        user = Utilisateur.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            telephone=validated_data['telephone'],
            password=make_password(validated_data['password'])
        )
        return user



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = Utilisateur
        fields = [ 'username', 'email', 'telephone','password','nom', 'prenom','date_naissance']

    def create(self, validated_data):
        user = Utilisateur.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            telephone=validated_data['telephone'],
            password=make_password(validated_data['password']),
            nom=validated_data.get('nom', ''),
            prenom=validated_data.get('prenom', ''),
            date_naissance=validated_data.get('date_naissance', None)                  
        )
        return user



class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class DemandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Demande
        fields = '__all__'

class PaiementCreateSerializer(serializers.ModelSerializer):
    demande_id = serializers.PrimaryKeyRelatedField(
        queryset=Demande.objects.all(),
        source="demande",
        write_only=True
    )

    class Meta:
        model = Paiement
        fields = ("demande_id", "montant", "methode", "transaction_id")

    def validate(self, attrs):
        demande = attrs["demande"]
        utilisateur = self.context["request"].user
        if demande.utilisateur != utilisateur and not utilisateur.is_staff:
            raise ValidationError("Vous ne pouvez payer que vos propres demandes.")
        if hasattr(demande, "paiement"):
            raise ValidationError("Cette demande a déjà été payée.")
        if attrs["montant"] != demande.service.prix:
            raise ValidationError("Le montant doit correspondre au prix du service.")
        return attrs

    def create(self, validated_data):
        demande = validated_data["demande"]
        paiement = Paiement.objects.create(
            **validated_data,
            statut="SUCCES"
        )
        demande.statut = "ACCEPTEE"
        demande.save(update_fields=["statut"])
        return paiement

class PaiementListSerializer(serializers.ModelSerializer):
    demande = DemandeSerializer()
    utilisateur = serializers.CharField(source="demande.utilisateur.username")

    class Meta:
        model = Paiement
        fields = (
            "id",
            "demande",
            "utilisateur",
            "montant",
            "methode",
            "transaction_id",
            "statut",
            "created_at",
        )