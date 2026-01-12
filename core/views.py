from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Demande, Paiement, Service, Utilisateur
from .serializers import ChangePasswordSerializer, DemandeSerializer, PaiementCreateSerializer, PaiementListSerializer, ServiceSerializer, UtilisateurSerializer, RegisterSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework import generics, permissions
from django.core.mail import send_mail
from django.conf import settings
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


# Change password
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # Verify old password
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"error": "L'ancien mot de passe est incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({"message": "Mot de passe changé avec succès."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        
        # Send email notification
        try:
            subject = "Nouvelle demande créée - GTAP"
            
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 28px; }}
                    .body {{ padding: 30px; background-color: #f9f9f9; }}
                    .body-content {{ background-color: white; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
                    .details {{ margin-top: 20px; }}
                    .detail-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
                    .detail-label {{ font-weight: bold; color: #333; }}
                    .detail-value {{ color: #666; }}
                    .footer {{ background-color: #333; color: white; padding: 20px; text-align: center; font-size: 12px; }}
                    .footer p {{ margin: 5px 0; }}
                    .footer a {{ color: #667eea; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <!-- HEADER -->
                    <div class="header">
                        <h1>🎯 GTAP - Nouvelle Demande</h1>
                    </div>
                    
                    <!-- BODY -->
                    <div class="body">
                        <div class="body-content">
                            <p>Bonjour <strong>{request.user.get_full_name() or request.user.username}</strong>,</p>
                            <p>Votre demande a été <strong style="color: #28a745;">créée avec succès</strong>!</p>
                            
                            <div class="details">
                                <div class="detail-row">
                                    <span class="detail-label">ID Demande:</span>
                                    <span class="detail-value"># {demande.id}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Service:</span>
                                    <span class="detail-value">{service.titre}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Prix:</span>
                                    <span class="detail-value">{service.prix} {service.devise}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Date:</span>
                                    <span class="detail-value">{demande.date.strftime('%d/%m/%Y à %H:%M')}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Statut:</span>
                                    <span class="detail-value"><strong style="color: #FFC107;">⏳ {demande.statut}</strong></span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Latitude:</span>
                                    <span class="detail-value">{latitude}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Longitude:</span>
                                    <span class="detail-value">{longitude}</span>
                                </div>
                            </div>
                            
                            <p style="margin-top: 20px; color: #666; font-size: 14px;">
                                Vous recevrez une notification dès que votre demande sera traitée.
                            </p>
                        </div>
                    </div>
                    
                    <!-- FOOTER -->
                    <div class="footer">
                        <p><strong>GTAP - Service de Gestion</strong></p>
                        <p>gtaplit@gmail.com</p>
                        <p style="margin-top: 15px; border-top: 1px solid #555; padding-top: 10px;">
                            © 2026 GTAP. Tous droits réservés.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            send_mail(
                subject,
                f"Votre demande #{demande.id} a été créée avec succès!",
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi du mail: {e}")
        
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