from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .Serializer import AdminTypeSerializer, AdminLoginSerializer, DepartmentSerializer, EmployeeSerializer, DoctorSerializer, ReceptionistSerializer, HelperSerializer, PatientSerializer, CheckLoginSerializer
from .models import AdminType, AdminLogin, Department, Employee, Doctor, Receptionist, Helper, Patient, CheckLogin
from drf_yasg.utils import swagger_auto_schema
from .authentication import (
    AuthenticationError,
    apply_auth_cookies,
    authenticate_user,
    clear_auth_cookies,
    decode_jwt_token,
    get_actor_from_payload,
    issue_token_pair,
)

# Create your views here.
class AllAdminType(APIView):
    @swagger_auto_schema(
        operation_description= "Get all admins",
        responses={200: AdminLoginSerializer(many=True)}
)
    
    def get(self, request):
        admins = AdminType.objects.all()
        if not admins.exists():
            return Response({'message': 'There is no AdminType in the database'}, status=status.HTTP_404_NOT_FOUND)
        serialize = AdminTypeSerializer(admins, many=True)
        return Response(serialize.data, status=status.HTTP_200_OK)
    
class AdminTypeById(APIView):
    @swagger_auto_schema(
        operation_description= "Get  admin types by Id",
        responses={200: AdminTypeSerializer}
)
    
    def get(self, request, Id):
        try:
            adminbyid = AdminType.objects.get(Id=Id)
        except AdminType.DoesNotExist:
            return Response({'message': f'Admin Id {Id} is not found'}, status=status.HTTP_404_NOT_FOUND)
        serialize = AdminTypeSerializer(adminbyid)
        return Response(serialize.data, status=status.HTTP_200_OK)
    

class CreateAdminType(APIView):
    @swagger_auto_schema(
        operation_description="Insert a new Admin Type",
        request_body=AdminTypeSerializer,
        responses={201: AdminTypeSerializer()}
    )
    def post(self, request):
        serialize = AdminTypeSerializer(data=request.data)
        if serialize.is_valid():
            serialize.save()
            return Response(serialize.data, status=status.HTTP_201_CREATED)
        return Response(serialize.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UpdateAdminType(APIView):
    @swagger_auto_schema(
        operation_description="Update an existing Admin Type",
        request_body=AdminTypeSerializer,
        responses={200: AdminTypeSerializer()}
    )
    def put(self, request):
        try:
            admin = AdminType.objects.get(Id=request.data.get('Id'))
        except AdminType.DoesNotExist:
            return Response(
                {'message': f'Admin ID {request.data.get("Id")} is not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminTypeSerializer(admin, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'AdminType updated successfully', 'data': serializer.data},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class DeleteAdminType(APIView):
    @swagger_auto_schema(
        operation_description="Delete an Admin Type by ID",
        responses={200: 'Admin Type deleted successfully'}
    )
    def delete(self, request, Id):
        try:
            admin = AdminType.objects.get(Id=Id)
        except AdminType.DoesNotExist:
            return Response({'message': f'Admin ID {Id} is not found'}, status=status.HTTP_404_NOT_FOUND)

        admin.delete()
        return Response({'message': f'Admin ID {Id} deleted successfully'}, status=status.HTTP_200_OK)
    
    

class AllAdminLogin(APIView):
    @swagger_auto_schema(
        operation_description= "Get all admin types",
        responses={200: AdminLoginSerializer(many=True)}
)
    
    def get(self, request):
        adminlogin = AdminLogin.objects.all()
        if not adminlogin.exists():
            return Response({'message': 'There is no Admins in the database'}, status=status.HTTP_404_NOT_FOUND)
        serialize = AdminLoginSerializer(adminlogin, many=True)
        return Response(serialize.data, status=status.HTTP_200_OK)
    
class AdminById(APIView):
    @swagger_auto_schema(
        operation_description= "Get  admin types by Id",
        responses={200: AdminLoginSerializer}
)
    
    def get(self, request, Id):
        try:
            adminbyid = AdminLogin.objects.get(Id=Id)
        except AdminLogin.DoesNotExist:
            return Response({'message': f'Admin Id {Id} is not found'}, status=status.HTTP_404_NOT_FOUND)
        serialize = AdminLoginSerializer(adminbyid)
        return Response(serialize.data, status=status.HTTP_200_OK)
    

class CreateAdmin(APIView):
    @swagger_auto_schema(
        operation_description="Insert a new Admin",
        request_body=AdminLoginSerializer,
        responses={201: AdminLoginSerializer()}
    )
    def post(self, request):
        serialize = AdminLoginSerializer(data=request.data)
        if serialize.is_valid():
            serialize.save()
            return Response(serialize.data, status=status.HTTP_201_CREATED)
        return Response(serialize.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UpdateAdmin(APIView):
    @swagger_auto_schema(
        operation_description="Update an existing Admin",
        request_body=AdminLoginSerializer,
        responses={200: AdminLoginSerializer()}
    )
    def put(self, request):
        try:
            admin = AdminLogin.objects.get(Id=request.data.get('Id'))
        except AdminLogin.DoesNotExist:
            return Response(
                {'message': f'Admin ID {request.data.get("Id")} is not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminLoginSerializer(admin, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Admin updated successfully', 'data': serializer.data},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class DeleteAdmin(APIView):
    @swagger_auto_schema(
        operation_description="Delete an Admin by ID",
        responses={200: 'Admin deleted successfully'}
    )
    def delete(self, request, Id):
        try:
            admin = AdminLogin.objects.get(Id=Id)
        except AdminLogin.DoesNotExist:
            return Response({'message': f'Admin ID {Id} is not found'}, status=status.HTTP_404_NOT_FOUND)

        admin.delete()
        return Response({'message': f'Admin ID {Id} deleted successfully'}, status=status.HTTP_200_OK)


class RegisterAdmin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CheckLoginSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Admin registered successfully. Please wait for activation."},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AdminLoginAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("Email") or request.data.get("email")
        password = request.data.get("Password") or request.data.get("password")
        remember_me = bool(request.data.get("remember_me"))

        result = authenticate_user(email, password)
        if result["status"] == "inactive_admin":
            admin = result["user"]
            return Response({
                "message": "Admin not activated",
                "admin_id": admin.id,
                "status": False,
            }, status=status.HTTP_403_FORBIDDEN)

        if result["status"] in {"inactive_staff", "password_not_set"}:
            return Response({
                "message": result["message"],
                "status": False,
            }, status=status.HTTP_403_FORBIDDEN)

        if result["status"] != "ok":
            return Response({
                "message": "Invalid credentials. Please register.",
                "status": False,
            }, status=status.HTTP_401_UNAUTHORIZED)

        payload = result["payload"]
        tokens = issue_token_pair(payload, remember_me=remember_me)
        response = Response({
            "message": "Login successful",
            "status": True,
            "role": payload["role"],
            "user_type": payload["user_type"],
            "user_id": payload["user_id"],
            "email": payload["email"],
            "display_name": payload["display_name"],
            "access": tokens["access"],
            "refresh": tokens["refresh"],
        }, status=status.HTTP_200_OK)
        return apply_auth_cookies(response, tokens, remember_me=remember_me)


class TokenRefreshAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh") or request.COOKIES.get("hcls_refresh_token")
        if not refresh_token:
            return Response({"message": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = decode_jwt_token(refresh_token, expected_type="refresh")
        except AuthenticationError as exc:
            return Response({"message": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        actor = get_actor_from_payload(payload)
        if not actor:
            return Response({"message": "User not found or inactive."}, status=status.HTTP_401_UNAUTHORIZED)

        actor_payload = {
            "user_type": actor.user_type,
            "user_id": actor.user_id,
            "role": actor.role,
            "email": actor.email,
            "display_name": actor.display_name,
        }
        tokens = issue_token_pair(actor_payload)
        response = Response({"access": tokens["access"], "refresh": tokens["refresh"]}, status=status.HTTP_200_OK)
        return apply_auth_cookies(response, tokens)


class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return clear_auth_cookies(Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK))


class CurrentActorAPIView(APIView):
    def get(self, request):
        actor = request.user
        return Response({
            "user_id": actor.user_id,
            "user_type": actor.user_type,
            "role": actor.role,
            "email": actor.email,
            "display_name": actor.display_name,
        }, status=status.HTTP_200_OK)
