from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Demande, Paiement, Service, Utilisateur
from .serializers import DemandeSerializer, PaiementCreateSerializer, PaiementListSerializer, ServiceSerializer, UtilisateurSerializer, RegisterSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework import generics, permissions
# Sign up
class SignUpView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Créer un token JWT automatiquement à l'inscription
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Utilisateur créé avec succès",
                "token": "Bearer " + str(refresh.access_token),
                "user": UtilisateurSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Login
class LoginView(APIView):
    def post(self, request):
        identifier = request.data.get('username')  # can be username or email
        password = request.data.get('password')

        if not identifier or not password:
            return Response({"error": "Veuillez fournir un nom d'utilisateur/email et un mot de passe."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Determine if the identifier is an email
        if '@' in identifier:
            try:
                user_obj = Utilisateur.objects.get(email__iexact=identifier)
                username = user_obj.username
            except Utilisateur.DoesNotExist:
                return Response({"error": "Aucun utilisateur trouvé avec cet email."},
                                status=status.HTTP_401_UNAUTHORIZED)
        else:
            username = identifier

        # Authenticate using username and password
        user = authenticate(username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "token": "Bearer " + str(refresh.access_token),
                "user": UtilisateurSerializer(user).data
            }, status=status.HTTP_200_OK)

        return Response({"error": "Nom d'utilisateur, email ou mot de passe incorrect."},
                        status=status.HTTP_401_UNAUTHORIZED)

# User info (JWT required)
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = UtilisateurSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ServiceListView(APIView):
    def get(self, request):
        services = Service.objects.filter(actif=True)  # seulement actifs
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
  

# Créer une demande
class CreateDemandeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        service_id = request.data.get('service')
        longitude = request.data.get('longitude')
        latitude = request.data.get('latitude')
 
        try:
            service = Service.objects.get(id=service_id, actif=True)
        except Service.DoesNotExist:
            return Response({"error": "Service non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        
        demande = Demande.objects.create(
            utilisateur=request.user,
            service=service,
            longitude=longitude,
            latitude=latitude
        )
        serializer = DemandeSerializer(demande)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CancelDemandeView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            demande = Demande.objects.get(id=pk, utilisateur=request.user)
        except Demande.DoesNotExist:
            return Response({"error": "Demande non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        
        if demande.statut != "EN_ATTENTE":
            return Response({"error": "Impossible d'annuler cette demande"}, status=status.HTTP_400_BAD_REQUEST)
        
        demande.statut = "REFUSEE"
        demande.save()
        serializer = DemandeSerializer(demande)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class PaiementCreateView(generics.CreateAPIView):
    """
    Crée un paiement pour une demande.
    L'utilisateur doit être connecté.
    """
    queryset = Paiement.objects.all()
    serializer_class = PaiementCreateSerializer
    permission_classes = []
    

class PaiementListView(generics.ListAPIView):
    queryset = Paiement.objects.all().select_related("demande", "demande__utilisateur")
    serializer_class = PaiementListSerializer
    permission_classes = [IsAuthenticated]