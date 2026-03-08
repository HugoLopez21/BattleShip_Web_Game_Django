
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('panel_admin/', include('admin_panel.urls')),
    path('', include('inicial.urls')),
    path('juego/', include('partida.urls'))
]
