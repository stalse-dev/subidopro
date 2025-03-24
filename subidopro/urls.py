from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', include('users.urls')),
    path('api/', include('api.urls')),
    path('ft/', include('frontend.urls')),
    path('', include('subidometro.urls')),
    path('', include('alunos.urls')),
]
