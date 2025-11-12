from django.urls import path
from .views import CancelDemandeView, CreateDemandeView, PaiementCreateView, ServiceListView, SignUpView, LoginView, UserDetailView,PaiementListView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', UserDetailView.as_view(), name='user-detail'),
    path('services/', ServiceListView.as_view(), name='services-detail'),
    
    
    path('demandes/', CreateDemandeView.as_view(), name='create-demande'),
    path('demandes/<int:pk>/cancel/', CancelDemandeView.as_view(), name='cancel-demande'),
    
    path("paiements/creer/", PaiementCreateView.as_view(), name="paiement-creer"),
    path("paiements/get/", PaiementListView.as_view(), name="paiement-get"),

]

