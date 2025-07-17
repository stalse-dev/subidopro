from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from subidometro.models import *
from rest_framework import status
from .serializers import *

class AlunoClienteCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AlunoClientesSerializer,
        responses=AlunoClientesSerializer   
    )
    def post(self, request):
        serializer = AlunoClientesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AlunoClienteDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Aluno_clientes, pk=pk)
    
    def get(self, request, pk):
        cliente = self.get_object(pk)
        serializer = AlunoClientesSerializer(cliente)
        return Response(serializer.data)
    
    @extend_schema(
        request=AlunoClientesSerializer,
        responses=AlunoClientesSerializer   
    )
    def put(self, request, pk):
        cliente = self.get_object(pk)
        serializer = AlunoClientesSerializer(cliente, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        request=AlunoClientesSerializer,
        responses=AlunoClientesSerializer,
        description="Atualiza parcialmente um cliente existente (PATCH)."
    )
    def patch(self, request, pk):
        cliente = self.get_object(pk)
        serializer = AlunoClientesSerializer(cliente, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        cliente = self.get_object(pk)
        cliente.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class AlunoClientesContratosAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AlunoClientesContratosSerializer,
        responses=AlunoClientesContratosSerializer   
    )
    def post(self, request):
        serializer = AlunoClientesContratosSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AlunoClientesContratosDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Aluno_clientes_contratos, pk=pk)
    
    def get(self, request, pk):
        contrato = self.get_object(pk)
        serializer = AlunoClientesContratosSerializer(contrato)
        return Response(serializer.data)
    
    @extend_schema(
        request=AlunoClientesContratosSerializer,
        responses=AlunoClientesContratosSerializer   
    )
    def put(self, request, pk):
        contrato = self.get_object(pk)
        serializer = AlunoClientesContratosSerializer(contrato, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        request=AlunoClientesContratosSerializer,
        responses=AlunoClientesContratosSerializer,
        description="Atualiza parcialmente um contrato existente (PATCH)."
    )
    def patch(self, request, pk):
        contrato = self.get_object(pk)
        serializer = AlunoClientesContratosSerializer(contrato, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        contrato = self.get_object(pk)
        contrato.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AlunoEnvioCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AlunoEnvioSerializer,
        responses=AlunoEnvioSerializer   
    )
    def post(self, request):
        serializer = AlunoEnvioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AlunoEnvioDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Aluno_envios, pk=pk)
    
    def get(self, request, pk):
        envio = self.get_object(pk)
        serializer = AlunoEnvioSerializer(envio)
        return Response(serializer.data)
    
    @extend_schema(
        request=AlunoEnvioSerializer,
        responses=AlunoEnvioSerializer   
    )
    def put(self, request, pk):
        envio = self.get_object(pk)
        serializer = AlunoEnvioSerializer(envio, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        request=AlunoEnvioSerializer,
        responses=AlunoEnvioSerializer,
        description="Atualiza parcialmente um envio existente (PATCH)."
    )
    def patch(self, request, pk):
        envio = self.get_object(pk)
        serializer = AlunoEnvioSerializer(envio, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        envio = self.get_object(pk)
        envio.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)








