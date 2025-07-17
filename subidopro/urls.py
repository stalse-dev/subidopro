from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', include('users.urls'), name='Login'),
    path('api/v2/', include('apisubido.urls'), name="Paginas_Subido_PRO"),
    path('pontos/', include('apipontos.urls'), name="Paginas_Subido_PRO"),
    path('', include('subidometro.urls')),
    path('', include('alunos.urls')),
]
