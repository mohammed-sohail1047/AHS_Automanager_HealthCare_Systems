import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import authentication, exceptions

from .models import CheckLogin, Doctor, Helper, Receptionist, Patient


def normalize_admin_type(admin_type):
    if admin_type is None:
        return None

    admin_type_str = str(admin_type).strip().upper()
    if admin_type_str in {"MADMIN", "1", "MANAGER ADMIN"}:
        return "MADMIN"
    if admin_type_str in {"OPADMIN", "2", "OPERATOR ADMIN"}:
        return "OPADMIN"
    return admin_type_str


ACCESS_TOKEN_COOKIE = "hcls_access_token"
REFRESH_TOKEN_COOKIE = "hcls_refresh_token"
ACCESS_TOKEN_LIFETIME = timedelta(minutes=60)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)
REMEMBER_ME_REFRESH_LIFETIME = timedelta(days=30)


@dataclass
class AuthenticatedActor:
    user_type: str
    user_id: int
    role: str
    email: str
    display_name: str

    @property
    def is_authenticated(self):
        return True

    @property
    def id(self):
        return self.user_id


class AuthenticationError(Exception):
    pass


def _b64url_encode(raw_bytes):
    return base64.urlsafe_b64encode(raw_bytes).rstrip(b"=").decode("ascii")


def _b64url_decode(raw_text):
    padding = "=" * (-len(raw_text) % 4)
    return base64.urlsafe_b64decode((raw_text + padding).encode("ascii"))


def _json_dumps(payload):
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _sign(signing_input):
    key = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(key, signing_input.encode("ascii"), hashlib.sha256).digest()


def create_jwt_token(payload, token_type, lifetime):
    now = timezone.now()
    body = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
        "type": token_type,
    }
    header_segment = _b64url_encode(_json_dumps({"alg": "HS256", "typ": "JWT"}))
    payload_segment = _b64url_encode(_json_dumps(body))
    signing_input = f"{header_segment}.{payload_segment}"
    signature_segment = _b64url_encode(_sign(signing_input))
    return f"{signing_input}.{signature_segment}"


def decode_jwt_token(token, expected_type=None):
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise AuthenticationError("Malformed token.") from exc

    signing_input = f"{header_segment}.{payload_segment}"
    expected_signature = _b64url_encode(_sign(signing_input))
    if not hmac.compare_digest(expected_signature, signature_segment):
        raise AuthenticationError("Invalid token signature.")

    try:
        payload = json.loads(_b64url_decode(payload_segment))
    except (json.JSONDecodeError, ValueError) as exc:
        raise AuthenticationError("Invalid token payload.") from exc

    if expected_type and payload.get("type") != expected_type:
        raise AuthenticationError("Invalid token type.")

    if int(payload.get("exp", 0)) <= int(timezone.now().timestamp()):
        raise AuthenticationError("Token has expired.")

    return payload


def build_actor_payload(user_type, user_id, role, email, display_name):
    return {
        "user_type": user_type,
        "user_id": user_id,
        "role": role,
        "email": email,
        "display_name": display_name,
    }


def issue_token_pair(actor_payload, remember_me=False):
    refresh_lifetime = REMEMBER_ME_REFRESH_LIFETIME if remember_me else REFRESH_TOKEN_LIFETIME
    return {
        "access": create_jwt_token(actor_payload, "access", ACCESS_TOKEN_LIFETIME),
        "refresh": create_jwt_token(actor_payload, "refresh", refresh_lifetime),
    }


def apply_auth_cookies(response, tokens, remember_me=False):
    refresh_lifetime = REMEMBER_ME_REFRESH_LIFETIME if remember_me else REFRESH_TOKEN_LIFETIME
    secure = not settings.DEBUG
    response.set_cookie(
        ACCESS_TOKEN_COOKIE,
        tokens["access"],
        max_age=int(ACCESS_TOKEN_LIFETIME.total_seconds()),
        httponly=True,
        secure=secure,
        samesite="Lax",
    )
    response.set_cookie(
        REFRESH_TOKEN_COOKIE,
        tokens["refresh"],
        max_age=int(refresh_lifetime.total_seconds()),
        httponly=True,
        secure=secure,
        samesite="Lax",
    )
    return response


def clear_auth_cookies(response):
    response.delete_cookie(ACCESS_TOKEN_COOKIE)
    response.delete_cookie(REFRESH_TOKEN_COOKIE)
    return response


def get_dashboard_route_for_role(role):
    if not role:
        return "login"

    normalized = str(role).strip().upper()
    if normalized == "MADMIN":
        return "dashboard"
    if normalized == "OPADMIN":
        return "OAdashboard"
    if normalized == "DOCTOR":
        return "doctor_dashboard"
    if normalized == "RECEPTIONIST":
        return "receptionist_dashboard"
    if normalized == "HELPER":
        return "helper_dashboard"
    if normalized == "PATIENT":
        return "patient_dashboard"
    return "login"


def _build_admin_actor(admin):
    return build_actor_payload(
        user_type="admin",
        user_id=admin.id,
        role=normalize_admin_type(admin.admin_type),
        email=admin.email,
        display_name=admin.username or admin.email,
    )


def _build_doctor_actor(doctor):
    return build_actor_payload("doctor", doctor.DocID, "DOCTOR", doctor.Email, doctor.Dname)


def _build_receptionist_actor(receptionist):
    return build_actor_payload("receptionist", receptionist.RecID, "RECEPTIONIST", receptionist.Email, receptionist.Rname)


def _build_helper_actor(helper):
    return build_actor_payload("helper", helper.HelperID, "HELPER", helper.Email, helper.Hname)


def _build_patient_actor(patient):
    return build_actor_payload("patient", patient.PatientID, "PATIENT", patient.Email, patient.Pname)


def authenticate_user(email, password):
    if not email or not password:
        return {"status": "invalid"}

    admin = CheckLogin.objects.filter(email__iexact=email).first()
    if admin and admin.check_password(password):
        if not admin.status:
            return {"status": "inactive_admin", "user": admin}
        return {"status": "ok", "payload": _build_admin_actor(admin)}

    doctor = Doctor.objects.filter(Email__iexact=email).first()
    if doctor and doctor.check_password(password):
        if not doctor.Status:
            return {"status": "inactive_staff", "message": "Doctor account is inactive."}
        return {"status": "ok", "payload": _build_doctor_actor(doctor)}

    receptionist = Receptionist.objects.filter(Email__iexact=email).first()
    if receptionist and receptionist.check_password(password):
        if not receptionist.Status:
            return {"status": "inactive_staff", "message": "Receptionist account is inactive."}
        return {"status": "ok", "payload": _build_receptionist_actor(receptionist)}

    helper = Helper.objects.filter(Email__iexact=email).first()
    if helper and helper.check_password(password):
        if not helper.Status:
            return {"status": "inactive_staff", "message": "Helper account is inactive."}
        return {"status": "ok", "payload": _build_helper_actor(helper)}

    patient = Patient.objects.filter(Email__iexact=email).first()
    if patient and patient.check_password(password):
        if not patient.Status:
            return {"status": "inactive_staff", "message": "Patient account is inactive."}
        return {"status": "ok", "payload": _build_patient_actor(patient)}

    if Doctor.objects.filter(Email__iexact=email).exists() or Receptionist.objects.filter(Email__iexact=email).exists() or Helper.objects.filter(Email__iexact=email).exists() or Patient.objects.filter(Email__iexact=email).exists():
        return {"status": "password_not_set", "message": "This account does not have a usable password yet."}

    return {"status": "invalid"}


def get_actor_from_payload(payload):
    user_type = payload.get("user_type")
    user_id = payload.get("user_id")
    email = payload.get("email")

    if user_type == "admin":
        admin = CheckLogin.objects.filter(id=user_id, email__iexact=email, status=True).first()
        return AuthenticatedActor(**_build_admin_actor(admin)) if admin else None

    if user_type == "doctor":
        doctor = Doctor.objects.filter(DocID=user_id, Email__iexact=email, Status=True).first()
        return AuthenticatedActor(**_build_doctor_actor(doctor)) if doctor else None

    if user_type == "receptionist":
        receptionist = Receptionist.objects.filter(RecID=user_id, Email__iexact=email, Status=True).first()
        return AuthenticatedActor(**_build_receptionist_actor(receptionist)) if receptionist else None

    if user_type == "helper":
        helper = Helper.objects.filter(HelperID=user_id, Email__iexact=email, Status=True).first()
        return AuthenticatedActor(**_build_helper_actor(helper)) if helper else None

    if user_type == "patient":
        patient = Patient.objects.filter(PatientID=user_id, Email__iexact=email, Status=True).first()
        return AuthenticatedActor(**_build_patient_actor(patient)) if patient else None

    return None


def get_request_actor(request):
    token = request.COOKIES.get(ACCESS_TOKEN_COOKIE)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    if not token:
        return None

    try:
        payload = decode_jwt_token(token, expected_type="access")
    except AuthenticationError:
        return None

    return get_actor_from_payload(payload)


def get_account_for_password_reset(email):
    admin = CheckLogin.objects.filter(email__iexact=email).first()
    if admin:
        return admin, "admin"

    doctor = Doctor.objects.filter(Email__iexact=email).first()
    if doctor:
        return doctor, "doctor"

    receptionist = Receptionist.objects.filter(Email__iexact=email).first()
    if receptionist:
        return receptionist, "receptionist"

    helper = Helper.objects.filter(Email__iexact=email).first()
    if helper:
        return helper, "helper"

    patient = Patient.objects.filter(Email__iexact=email).first()
    if patient:
        return patient, "patient"

    return None, None


def set_account_password(account, account_type, password):
    if account_type == "admin":
        account.password = password
    else:
        account.Password = password
    account.save()


class HospitalJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).decode("utf-8")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        else:
            token = request.COOKIES.get(ACCESS_TOKEN_COOKIE)
            if not token:
                return None

        try:
            payload = decode_jwt_token(token, expected_type="access")
        except AuthenticationError as exc:
            raise exceptions.AuthenticationFailed(str(exc)) from exc

        actor = get_actor_from_payload(payload)
        if not actor:
            raise exceptions.AuthenticationFailed("User not found or inactive.")

        return actor, payload
