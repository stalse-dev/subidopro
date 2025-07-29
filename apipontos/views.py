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
    serializer_class = AlunoClientesSerializer

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
    serializer_class = AlunoClientesSerializer


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
    serializer_class = AlunoClientesContratosSerializer

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
    serializer_class = AlunoClientesContratosSerializer

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
    serializer_class = AlunoEnvioSerializer

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
    serializer_class = AlunoEnvioSerializer

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

class AlunoDesafioCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlunoDesafioSerializer

    @extend_schema(
        request=AlunoDesafioSerializer,
        responses=AlunoDesafioSerializer   
    )
    def post(self, request):
        serializer = AlunoDesafioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AlunoDesafioDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlunoDesafioSerializer

    def get_object(self, pk):
        return get_object_or_404(Aluno_desafio, pk=pk)
    
    def get(self, request, pk): 
        desafio = self.get_object(pk)
        serializer = AlunoDesafioSerializer(desafio)
        return Response(serializer.data)
    
    @extend_schema(
        request=AlunoDesafioSerializer,
        responses=AlunoDesafioSerializer   
    )
    def put(self, request, pk):
        desafio = self.get_object(pk)
        serializer = AlunoDesafioSerializer(desafio, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        request=AlunoDesafioSerializer,
        responses=AlunoDesafioSerializer,
        description="Atualiza parcialmente um desafio existente (PATCH)."
    )
    def patch(self, request, pk):
        desafio = self.get_object(pk)
        serializer = AlunoDesafioSerializer(desafio, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        desafio = self.get_object(pk)
        desafio.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AlunoCertificacaoCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlunoCertificacaoSerializer

    @extend_schema(
        request=AlunoCertificacaoSerializer,
        responses=AlunoCertificacaoSerializer
    )
    def post(self, request):
        serializer = AlunoCertificacaoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AlunoCertificacaoDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlunoCertificacaoSerializer

    def get_object(self, pk):
        return get_object_or_404(Aluno_certificacao, pk=pk)
    
    def get(self, request, pk):
        certificacao = self.get_object(pk)
        serializer = AlunoCertificacaoSerializer(certificacao)
        return Response(serializer.data)
    
    @extend_schema(
        request=AlunoCertificacaoSerializer,
        responses=AlunoCertificacaoSerializer   
    )
    def put(self, request, pk):
        certificacao = self.get_object(pk)
        serializer = AlunoCertificacaoSerializer(certificacao, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        request=AlunoCertificacaoSerializer,
        responses=AlunoCertificacaoSerializer,
        description="Atualiza parcialmente uma certificação existente (PATCH)."
    )
    def patch(self, request, pk):
        certificacao = self.get_object(pk)
        serializer = AlunoCertificacaoSerializer(certificacao, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        certificacao = self.get_object(pk)
        certificacao.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AlunoManualCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlunoManualSerializer

    @extend_schema(
        request=AlunoManualSerializer,
        responses=AlunoManualSerializer   
    )
    def post(self, request):
        serializer = AlunoManualSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AlunoManualDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlunoManualSerializer

    def get_object(self, pk):
        return get_object_or_404(Aluno_certificacao, pk=pk)
    
    def get(self, request, pk):
        manual = self.get_object(pk)
        serializer = AlunoManualSerializer(manual)
        return Response(serializer.data)
    
    @extend_schema(
        request=AlunoManualSerializer,
        responses=AlunoManualSerializer   
    )
    def put(self, request, pk):
        manual = self.get_object(pk)
        serializer = AlunoManualSerializer(manual, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        request=AlunoManualSerializer,
        responses=AlunoManualSerializer,
        description="Atualiza parcialmente um manual existente (PATCH)."
    )
    def patch(self, request, pk):
        manual = self.get_object(pk)
        serializer = AlunoManualSerializer(manual, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        manual = self.get_object(pk)
        manual.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AlunoCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlunoSerializer

    @extend_schema(request=AlunoSerializer, responses=AlunoSerializer)
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
 
class AlunoDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlunoSerializer

    def get_object(self, pk):
        return get_object_or_404(Alunos, pk=pk)
    
    def get(self, request, pk):
        aluno = self.get_object(pk)
        serializer = AlunoSerializer(aluno)
        return Response(serializer.data)
    
    @extend_schema(
        request=AlunoSerializer,
        responses=AlunoSerializer   
    )
    def put(self, request, pk):
        aluno = self.get_object(pk)
        serializer = AlunoSerializer(aluno, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        request=AlunoSerializer,
        responses=AlunoSerializer,
        description="Atualiza parcialmente um aluno existente (PATCH)."
    )
    def patch(self, request, pk):
        aluno = self.get_object(pk)
        serializer = AlunoSerializer(aluno, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        aluno = self.get_object(pk)
        aluno.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class DesafioCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DesafioSerializer

    @extend_schema(
        request=DesafioSerializer,
        responses=DesafioSerializer
    )
    def post(self, request):
        serializer = DesafioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class DesafioDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DesafioSerializer

    def get_object(self, pk):
        return get_object_or_404(Desafios, pk=pk)

    def get(self, request, pk):
        desafio = self.get_object(pk)
        serializer = DesafioSerializer(desafio)
        return Response(serializer.data)

    @extend_schema(
        request=DesafioSerializer,
        responses=DesafioSerializer
    )
    def put(self, request, pk):
        desafio = self.get_object(pk)
        serializer = DesafioSerializer(desafio, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=DesafioSerializer,
        responses=DesafioSerializer,
        description="Atualiza parcialmente um desafio existente (PATCH)."
    )
    def patch(self, request, pk):
        desafio = self.get_object(pk)
        serializer = DesafioSerializer(desafio, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        desafio = self.get_object(pk)
        desafio.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

