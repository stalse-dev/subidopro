from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', include('users.urls')),
    path('api/v2/', include('apisubido.urls')),
    path('', include('subidometro.urls')),
    path('', include('alunos.urls')),
]
