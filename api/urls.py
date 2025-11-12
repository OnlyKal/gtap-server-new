from django.urls import path, include

urlpatterns = [
    path('lit/', include('core.urls')),
]