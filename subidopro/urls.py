from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', include('users.urls'), name='Login'),
    path('api/', include('api.urls'), name="API INVENTANDUS"),
    path('api/v2/', include('apisubido.urls'), name="Paginas_Subido_PRO"),
    path('pontos/', include('apipontos.urls'), name="Paginas_Subido_PRO"),
    path('', include('subidometro.urls')),
    path('calculadora_pontos/', include('calculadora_pontos.urls')),
    path('', include('alunos.urls')),
    path('teste/', include('teste_app.urls'))
]