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
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 20px auto; background-color: white; }}
                    .header {{ background-color: #27ae60; color: white; padding: 40px 20px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 32px; font-weight: 600; }}
                    .header p {{ margin: 10px 0 0 0; font-size: 16px; opacity: 0.95; }}
                    .header-divider {{ height: 4px; background-color: #229954; margin-top: 15px; }}
                    .body {{ padding: 40px; }}
                    .greeting {{ font-size: 18px; color: #2c3e50; margin-bottom: 25px; }}
                    .greeting strong {{ color: #27ae60; }}
                    .status-box {{ background-color: #f0fdf4; border-left: 5px solid #27ae60; padding: 15px; margin-bottom: 30px; }}
                    .status-text {{ color: #27ae60; font-weight: 600; font-size: 16px; margin: 0; }}
                    .details-section {{ margin-bottom: 30px; }}
                    .details-title {{ color: #27ae60; font-weight: 600; font-size: 14px; text-transform: uppercase; margin-bottom: 15px; letter-spacing: 1px; }}
                    .detail-item {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #ecf0f1; }}
                    .detail-item:last-child {{ border-bottom: none; }}
                    .detail-label {{ color: #7f8c8d; font-weight: 500; font-size: 14px; }}
                    .detail-value {{ color: #2c3e50; font-weight: 600; font-size: 14px; text-align: right; }}
                    .info-box {{ background-color: #fef5e7; border-left: 5px solid #f39c12; padding: 15px; margin-top: 30px; margin-bottom: 30px; }}
                    .info-text {{ color: #7d6608; font-size: 13px; margin: 0; }}
                    .divider {{ height: 1px; background-color: #ecf0f1; margin: 30px 0; }}
                    .footer {{ background-color: #2c3e50; color: white; padding: 30px 20px; text-align: center; }}
                    .footer p {{ margin: 8px 0; font-size: 13px; }}
                    .footer-title {{ font-size: 14px; font-weight: 600; margin-bottom: 15px; }}
                    .footer-contact {{ color: #ecf0f1; margin-top: 15px; }}
                    .footer-divider {{ height: 1px; background-color: #34495e; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <!-- HEADER -->
                    <div class="header">
                        <h1>✓ DEMANDE CRÉÉE</h1>
                        <p>Votre demande a été enregistrée avec succès</p>
                        <div class="header-divider"></div>
                    </div>
                    
                    <!-- BODY -->
                    <div class="body">
                        <p class="greeting">Bienvenue <strong>{request.user.get_full_name() or request.user.username}</strong>,</p>
                        
                        <div class="status-box">
                            <p class="status-text">✓ Votre demande a été enregistrée et est en attente de traitement</p>
                        </div>
                        
                        <!-- Identifiant Section -->
                        <div class="details-section">
                            <div class="details-title">Numéro de Demande</div>
                            <div class="detail-item">
                                <span class="detail-label">ID:</span>
                                <span class="detail-value">GTAP-{demande.id:06d}</span>
                            </div>
                        </div>
                        
                        <!-- Service Section -->
                        <div class="details-section">
                            <div class="details-title">Détails du Service</div>
                            <div class="detail-item">
                                <span class="detail-label">Service:</span>
                                <span class="detail-value">{service.titre}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Prix:</span>
                                <span class="detail-value">{service.prix} {service.devise}</span>
                            </div>
                        </div>
                        
                        <!-- Localisation Section -->
                        <div class="details-section">
                            <div class="details-title">Localisation</div>
                            <div class="detail-item">
                                <span class="detail-label">Latitude:</span>
                                <span class="detail-value">{latitude}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Longitude:</span>
                                <span class="detail-value">{longitude}</span>
                            </div>
                        </div>
                        
                        <!-- Date & Statut Section -->
                        <div class="details-section">
                            <div class="details-title">Information</div>
                            <div class="detail-item">
                                <span class="detail-label">Date:</span>
                                <span class="detail-value">{demande.date.strftime('%d/%m/%Y à %H:%M')}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Statut:</span>
                                <span class="detail-value" style="color: #f39c12;">EN ATTENTE</span>
                            </div>
                        </div>
                        
                        <div class="info-box">
                            <p class="info-text">
                                <strong>Note:</strong> Vous recevrez une notification par email dès que votre demande sera traitée. 
                                Conservez votre numéro de demande pour vos références futures.
                            </p>
                        </div>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <!-- FOOTER -->
                    <div class="footer">
                        <div class="footer-title">GTAP - Gestion des Demandes</div>
                        <div class="footer-contact">
                            <p>📧 <strong>Email:</strong> gtaplit@gmail.com</p>
                            <p>📱 <strong>Service Client:</strong> Disponible 24/7</p>
                        </div>
                        <div class="footer-divider"></div>
                        <p style="margin-top: 20px; color: #bdc3c7; font-size: 12px;">
                            © 2026 GTAP. Tous droits réservés. | Gestion des demandes de service
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