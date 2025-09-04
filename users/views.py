from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import *
from django.views.decorators.csrf import csrf_exempt
from users.models import User
import json
from django.contrib import messages


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("campeonatos")
        else:
            messages.error(request, "E-mail ou senha inválidos.")

    return render(request, "Login/login.html")

def logout_view(request):
    logout(request)
    return redirect("login")

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(allow_cors, name='dispatch')
class LoginView(APIView):
    def post(self, request):
        tempo_inicio = time.time()
        email = request.data.get("email")
        if not email:
            response_info = build_standard_response(
                message="Email não listado",
                status=404,
                tempo_inicio=tempo_inicio
            )

            response_data = {
                "info": response_info,
                "message": "Email não obtido",
            }

            return JsonResponse(response_data, status=404)
        
        password = request.data.get("password")
        if not password:
            response_info = build_standard_response(
                message="Senha não obtida",
                status=404,
                tempo_inicio=tempo_inicio
            )

            response_data = {
                "info": response_info,
                "message": "Senha não obtida",
            }

            return JsonResponse(response_data, status=404)

        user = authenticate(email=email, password=password)

        if user is not None:
            refresh_token = RefreshToken.for_user(user)
            access_token = refresh_token.access_token

            response_info = build_standard_response(
                message="Tokens gerados com sucesso",
                status=200,
                tempo_inicio=tempo_inicio
            )

            response_data = {
                "info": response_info,
                "access_token": str(access_token),
                "refresh_token": str(refresh_token)
            }


            return JsonResponse(response_data, status=200)
        else:
            response_info = build_standard_response(
                message="Usuario não encontrado",
                status=404,
                tempo_inicio=tempo_inicio
            )

            response_data = {
                "info": response_info,
                "message": "Usuario não encontrado",
            }

            return JsonResponse(response_data, status=404)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(allow_cors, name='dispatch')
class RefreshTokenView(APIView):
    def post(self, request):
        tempo_inicio = time.time()
        request_data = json.loads(request.body.decode("utf-8"))
        refresh_token = request_data.get("refresh_token", None)

        if not refresh_token:
            response_info = build_standard_response(
                message="Token de refresh nao encontrado",
                status=401,
                tempo_inicio=tempo_inicio
            )

            response_data = {
                "info":  response_info,
                "error": "Token de refresh nao encontrado"
            }
            return JsonResponse(response_data, status=401)
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            # Decodificando o refresh token para obter o user_id
            user_id = refresh.payload.get("user_id")
            if not user_id:
                response_info = build_standard_response(
                    message="Token inválido",
                    status=401,
                    tempo_inicio=tempo_inicio
                )

                response_data = {
                    "info":  response_info,
                    "error": "Token inválido"
                }
                return JsonResponse(response_data, status=401)
            
            user = User.objects.get(id=user_id)
            user_data = {
                "email": user.email,
                "name": user.name
            }

            response_info = build_standard_response(
                message="Token atualizado com sucesso",
                status=200,
                tempo_inicio=tempo_inicio
            )
            
            response_data = {
                "info":  response_info,
                "user_data": user_data
                }
            
            response = JsonResponse(response_data, status=200)
            return response

        except Exception as e:
            response_info = build_standard_response(
                message="Token invalido ou expirado",
                status=500,
                tempo_inicio=tempo_inicio
            )

            response_data = {
                "info":  response_info,
                "error": "Token invalido ou expirado", "detail": str(e)
            }

            return JsonResponse(response_data, status=500)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(allow_cors, name='dispatch')
class LogoutView(APIView):
    def post(self, request):
        tempo_inicio = time.time()

        request_data = json.loads(request.body.decode("utf-8"))
        refresh_token = request_data.get("refresh_token", None)

        if not refresh_token:
            response_info = build_standard_response(
                message="Token de refresh não fornecido",
                status=400,
                tempo_inicio=tempo_inicio
            )
            return Response({"info": response_info, "error": "Token de refresh não fornecido"}, status=400)

        try:
            # Revoga o token de refresh
            token = RefreshToken(refresh_token)
            token.blacklist()  # Adiciona o token à blacklist (requer configuração no settings.py)

            response_info = build_standard_response(
                message="Logout realizado com sucesso",
                status=200,
                tempo_inicio=tempo_inicio
            )

            response = Response({"info": response_info, "message": "Logout realizado com sucesso"}, status=200)

            return response

        except Exception as e:
            response_info = build_standard_response(
                message="Erro ao fazer logout",
                status=500,
                tempo_inicio=tempo_inicio
            )
            return Response({"info": response_info, "error": "Token inválido ou já revogado", "detail": str(e)}, status=500)

    