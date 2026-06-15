from django.db.models import Q
from django.shortcuts import redirect, render
from HclsWebApi.models import (
    CheckLogin,
    PasswordResetToken,
    AdminLogin,
    AdminType,
    Patient,
    Doctor,
    Employee,
    Department,
    Receptionist,
    Helper,
)
from django.contrib import messages
from .decorators import login_required, mAdmin_only, opAdmin_only, already_authenticated, normalize_admin_type, doctor_only
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .repositories.django_admin_repository import DjangoAdminRepository
from HclsWebApi.authentication import (
    apply_auth_cookies,
    authenticate_user,
    clear_auth_cookies,
    get_account_for_password_reset,
    get_dashboard_route_for_role,
    issue_token_pair,
    set_account_password,
)
# from .decorators import login_required, already_authenticated, mAdmin_only, opAdmin_only


# Create your views here.


@already_authenticated
def home(request):
    return render(request, 'Admin/Anonymous/home.html')

@already_authenticated
def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        phone = request.POST.get('phone', '')
        admin_type = (request.POST.get('admin_type'))

        if CheckLogin.objects.filter(email=email).exists():
            return render(request, 'Admin/Anonymous/register.html', {
                'error': 'Email already exists'
            })

        repo = DjangoAdminRepository()
        new_check = repo.create_checklogin(email=email, username=username, password=password, phone=phone, admin_type=admin_type)
        try:
            repo.create_adminlogin_from_check(new_check)
        except Exception as e:
            print('Warning: failed to create AdminLogin record for new CheckLogin:', e)

        return render(request, 'Admin/Anonymous/login.html', {
            'success': 'Registration successful!'
        })

    return render(request, 'Admin/Anonymous/register.html')

        
    #     # Create AdminLogin record
    #     # Note: AdminType should be set based on your business logic (default to 1 for now)
    #     try:
    #         # Get the next available ID
    #         last_admin = AdminLogin.objects.order_by('-Id').first()
    #         next_id = (last_admin.Id + 1) if last_admin else 1
            
    #         AdminLogin.objects.create(
    #             Id=next_id,
    #             Name=username,
    #             Gender=gender,
    #             Password=password,
    #             Phone=phone,
    #             Email=email,
    #             Address=address,
    #             AdminType_id=1,  # Default AdminType ID
    #             Status=False
    #         )
    #         return render(request, 'Admin/Anonymous/login.html')
    #     except Exception as e:
    #         return render(request, 'Admin/Anonymous/register.html', {'error': str(e)})
    # return render(request, 'Admin/Anonymous/register.html')


@already_authenticated
def login(request):
    if request.method == "POST":
        email = request.POST.get('username')
        password = request.POST.get('password')

        remember_me = request.POST.get('remember') == 'on'
        result = authenticate_user(email, password)

        if result["status"] == "inactive_admin":
            # 🔥 redirect if not activated
            return redirect('activate_admin', id=result["user"].id)

        if result["status"] in {"inactive_staff", "password_not_set"}:
            return render(request, 'Admin/Anonymous/login.html', {'error': result["message"]})

        if result["status"] == "ok":
            payload = result["payload"]
            tokens = issue_token_pair(payload, remember_me=remember_me)
            response = redirect(get_dashboard_route_for_role(payload["role"]))
            return apply_auth_cookies(response, tokens, remember_me=remember_me)

        return render(request, 'Admin/Anonymous/login.html', {'error': 'Invalid credentials'})

    return render(request, 'Admin/Anonymous/login.html')

# def login(request):
#     if request.method == "POST":
#         email = request.POST.get('username')
#         password = request.POST.get('password')

#         user = CheckLogin.objects.filter(email=email, password=password).first()

#         if user and user.admin_type:
#             # ✅ Ensure status is True before setting session
#             if not user.status:
#                 return redirect('Admin/Anonymous/activate_admin.html',id=user.id)

#             # Normalize admin_type from database
#             normalized_type = normalize_admin_type(user.admin_type)
            
#             if not normalized_type:
#                 return render(request, 'Admin/Anonymous/login.html', {
#                     'error': 'Invalid admin type. Contact support.'
#                 })

#             request.session['admin_id'] = user.id
#             request.session['admin_type'] = normalized_type
#             request.session.modified = True

#             if normalized_type == "MADMIN":
#                 return redirect('dashboard')
#             elif normalized_type == "OPADMIN":
#                 return redirect('OAdashboard')

#         return render(request, 'Admin/Anonymous/login.html', {'error': 'Invalid credentials'})

#     return render(request, 'Admin/Anonymous/login.html')
# def login(request):

#     # 🚫 If already logged in → redirect
#     if request.session.get("admin_id"):
#         admin_type = request.session.get("admin_type")

#         if admin_type == "1":
#             return redirect("dashboard")
#         else:
#             return redirect("OAdashboard")

#     if request.method == "POST":
#         email = request.POST.get("username")
#         password = request.POST.get("password")

#         try:
#             admin = CheckLogin.objects.get(email=email, password=password)

#             # ❌ Not active → go to activation page
#             if not admin.status:
#                 return redirect("activate_admin", admin.id)

#             # ✅ Create session
#             request.session["admin_id"] = admin.id
#             request.session["admin_type"] = admin.admin_type

#             # 🎯 Redirect based on role
#             if admin.admin_type == "MAdmin":
#                 return redirect("dashboard")
#             else:
#                 return redirect("OAdashboard")

#         except CheckLogin.DoesNotExist:
#             return render(request, "Admin/Anonymous/login.html", {
#                 "error": "Invalid credentials"
#             })

#     return render(request, "Admin/Anonymous/login.html")

@already_authenticated
def activate_admin(request, id):
    admin = CheckLogin.objects.get(id=id)

    if request.method == "POST":
        password = request.POST.get("password")

        # Verify password using check_password method (compares with hashed password)
        if admin.check_password(password):
            admin.status = True
            admin.save()
            return redirect("login")

        else:
            return render(request, "Admin/Anonymous/activate_admin.html", {
                "admin": admin,
                "error": "Incorrect password"
            })

    return render(request, "Admin/Anonymous/activate_admin.html", {
        "admin": admin
    })

@mAdmin_only
def dashboard(request):
    admins = CheckLogin.objects.select_related('created_by').all()
    today = timezone.localdate()

    current_admin_id = request.current_actor.id
    opadmins = []
    active_count = 0
    inactive_count = 0

    for a in admins:
        if normalize_admin_type(a.admin_type) == 'OPADMIN':
            creator = getattr(a, 'created_by', None)
            # skip if this OpAdmin was not created by the current MAdmin
            if not current_admin_id or not creator or getattr(creator, 'id', None) != current_admin_id:
                continue

            if a.status:
                active_count += 1
            else:
                inactive_count += 1

            created_by_name = creator.username if getattr(creator, 'username', None) else (creator.email if creator else 'System')
            opadmins.append({
                'id': a.id,
                'name': a.username or a.email,
                'role': 'OpAdmin',
                'email': a.email,
                'phone': a.phone,
                'created_by': created_by_name,
                'created_on': getattr(a, 'created_on', None),
                'status': 'Active' if a.status else 'Inactive',
            })

    patient_count = Patient.objects.count()
    doctor_count = Doctor.objects.count()
    department_count = Department.objects.count()
    staff_count = Employee.objects.count() + Receptionist.objects.count() + Helper.objects.count()
    appointments_count = Patient.objects.filter(EntryDateandTime__date=today).count()
    admitted_count = Patient.objects.filter(IsAdmitted=True).count()
    discharged_count = Patient.objects.exclude(ExitDateandTime__isnull=True).count()
    total_opadmins = active_count + inactive_count
    activation_rate = round((active_count / total_opadmins) * 100) if total_opadmins else 0

    recent_patients = list(
        Patient.objects.select_related('DoctorID')
        .order_by('-EntryDateandTime')[:4]
    )
    recent_admins = CheckLogin.objects.filter(created_by_id=current_admin_id).order_by('-created_on')[:5]

    activity_feed = []
    for patient in recent_patients:
        activity_feed.append({
            'title': patient.Pname,
            'subtitle': f"Assigned to Dr. {patient.DoctorID.Dname}",
            'time': patient.EntryDateandTime,
            'state': 'Admitted' if patient.IsAdmitted else 'Checked in',
        })
    for admin in recent_admins:
        activity_feed.append({
            'title': admin.username or admin.email,
            'subtitle': 'Operational admin onboarded',
            'time': admin.created_on,
            'state': 'Active' if admin.status else 'Pending activation',
        })
    activity_feed = sorted(activity_feed, key=lambda item: item['time'], reverse=True)[:6]

    context = {
        'patients_count': patient_count,
        'doctors_count': doctor_count,
        'appointments_count': appointments_count,
        'staff_count': staff_count,
        'department_count': department_count,
        'admitted_count': admitted_count,
        'discharged_count': discharged_count,
        'activation_rate': activation_rate,
        'recent_activities': activity_feed,
        'opadmins': opadmins,
        'opadmin_active_count': active_count,
        'opadmin_inactive_count': inactive_count,
        'total_opadmins': total_opadmins,
        'focus_cards': [
            {
                'label': 'Capacity',
                'value': f'{admitted_count} admitted',
                'meta': f'{discharged_count} discharged',
                'tone': 'success',
            },
            {
                'label': 'Admin activation',
                'value': f'{activation_rate}%',
                'meta': f'{inactive_count} still pending',
                'tone': 'warning',
            },
            {
                'label': 'Departments',
                'value': department_count,
                'meta': f'{doctor_count} doctors mapped',
                'tone': 'info',
            },
        ],
    }

    return render(request, "Admin/MAdmin/dashboard.html", context)

@mAdmin_only
def profile(request):
    try:
        admin_id = request.current_actor.id
        admin = CheckLogin.objects.get(id=admin_id)
        password_modal_open = False
        password_message = None
        password_message_level = None

        # Handle POST from MAdmin profile edit form (save changes + avatar)
        if request.method == 'POST':
            form_type = request.POST.get('form_type')
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if form_type == 'change_password':
                password_modal_open = True

                if not current_password or not new_password or not confirm_password:
                    password_message = 'Please fill in all password fields.'
                    password_message_level = 'danger'
                elif not admin.check_password(current_password):
                    password_message = 'Current password is incorrect.'
                    password_message_level = 'danger'
                elif new_password != confirm_password:
                    password_message = 'New password and confirm password do not match.'
                    password_message_level = 'danger'
                elif len(new_password) < 8:
                    password_message = 'New password must be at least 8 characters long.'
                    password_message_level = 'danger'
                else:
                    try:
                        admin.password = new_password
                        admin.save()
                        messages.success(request, 'Password changed successfully.')
                        return redirect('profile')
                    except Exception as e:
                        print('Error changing MAdmin password:', str(e))
                        messages.error(request, f'Error changing password: {e}')
            else:
                name = request.POST.get('name')
                phone = request.POST.get('phone')
                address = request.POST.get('address')
                gender = request.POST.get('gender')
                avatar_file = request.FILES.get('avatar')

                print('MAdmin profile POST:', {'name': name, 'phone': phone, 'address': address, 'gender': gender, 'has_avatar': bool(avatar_file)})

                if name:
                    admin.username = name
                if phone is not None:
                    admin.phone = phone
                if address is not None:
                    admin.address = address
                if gender is not None:
                    admin.gender = gender
                if avatar_file:
                    admin.avatar = avatar_file

                try:
                    admin.save()
                    messages.success(request, 'Profile updated successfully.')
                    return redirect('profile')
                except Exception as e:
                    print('Error saving MAdmin profile:', str(e))
                    messages.error(request, f'Error saving profile: {e}')

        context = {
            'admin': admin,
            'admin_username': admin.username,
            'admin_email': admin.email,
            'password_modal_open': password_modal_open,
            'password_message': password_message,
            'password_message_level': password_message_level,
        }
    except CheckLogin.DoesNotExist:
        return clear_auth_cookies(redirect('login'))
    
    return render(request, 'Admin/MAdmin/profile_new.html', context)


@login_required
@mAdmin_only
def add_operational_admin(request):
    """View for MAdmin to add new Operational Admins"""
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone = request.POST.get('phone', '')

        # Validate passwords match
        if password != confirm_password:
            return render(request, 'Admin/MAdmin/add.html', {
                'error': 'Passwords do not match in the Operational Admin form'
            })

        # Check if email already exists
        if CheckLogin.objects.filter(email=email).exists():
            return render(request, 'Admin/MAdmin/add.html', {
                'error': 'Email already exists. Please use a different email address.'
            })

        # Check if username already exists
        if CheckLogin.objects.filter(username=username).exists():
            return render(request, 'Admin/MAdmin/add.html', {
                'error': 'Username already exists. Please choose a different username.'
            })

        # Create new Operational Admin
        # attach creator from session (if available)
        creator = None
        creator_id = request.current_actor.id
        if creator_id:
            creator = CheckLogin.objects.filter(id=creator_id).first()

        repo = DjangoAdminRepository()
        new_check = repo.create_checklogin(email=email, username=username, password=password, phone=phone, admin_type='2', created_by=creator)
        try:
            repo.create_adminlogin_from_check(new_check)
        except Exception as e:
            print('Warning: failed to create AdminLogin for OpAdmin:', e)

        return render(request, 'Admin/MAdmin/add.html', {
            'success': 'Operational Admin created successfully! They will receive an activation email.'
        })

    return render(request, 'Admin/MAdmin/add.html')

@login_required
@mAdmin_only
def add(request):
    return render(request, 'Admin/MAdmin/add.html')

@login_required
@mAdmin_only
def manage(request):
    # Show all Managerial and Operational admins to MAdmin users
    from django.core.paginator import Paginator

    # Fetch all potential admin records
    admins = CheckLogin.objects.all().order_by('-created_on')

    # scope: 'my' (only records created by current MAdmin) or 'all'
    scope = request.GET.get('scope', 'my')
    current_admin_id = request.current_actor.id

    # Build items list containing only Operational Admins with requested columns
    items = []
    for a in admins:
        if normalize_admin_type(a.admin_type) == 'OPADMIN':
            creator = a.created_by
            # if scope is 'my', only include those created by current admin
            if scope == 'my' and current_admin_id:
                if not creator or getattr(creator, 'id', None) != current_admin_id:
                    continue

            created_by_name = creator.username if creator and getattr(creator, 'username', None) else (creator.email if creator else 'System')
            items.append({
                'id': a.id,
                'name': a.username or a.email,
                'role': 'OpAdmin',
                'email': a.email,
                'phone': a.phone,
                'created_by': created_by_name,
                'created_on': getattr(a, 'created_on', None),
                'status': 'Active' if a.status else 'Inactive',
            })

    # Paginate results (25 per page)
    paginator = Paginator(items, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'items': page_obj.object_list,
        'page_obj': page_obj,
        'scope': scope,
    }
    return render(request, 'Admin/MAdmin/manage.html', context)


@login_required
@mAdmin_only
def edit(request, id):
    """Edit view for Manage table rows."""
    try:
        admin = CheckLogin.objects.get(id=id)
    except CheckLogin.DoesNotExist:
        messages.error(request, 'Record not found.')
        return redirect('manage')

    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        status = request.POST.get('status') == 'on'

        if email and email != admin.email and CheckLogin.objects.filter(email=email).exclude(id=id).exists():
            messages.error(request, 'Email already in use.')
        elif username and username != admin.username and CheckLogin.objects.filter(username=username).exclude(id=id).exists():
            messages.error(request, 'Username already in use.')
        else:
            admin.email = email
            admin.username = username
            admin.phone = phone
            admin.status = status
            admin.save()
            messages.success(request, 'Admin updated successfully.')
            return redirect('manage')

    return render(request, 'Admin/MAdmin/edit.html', {'admin': admin})

@login_required
@mAdmin_only
def delete_admin(request, id):
    if request.method == 'POST':
        try:
            admin = CheckLogin.objects.get(id=id)
            admin.delete()
            # Note: The database should ideally cascade delete AdminLogin, etc.
            messages.success(request, 'Admin deleted successfully.')
        except CheckLogin.DoesNotExist:
            messages.error(request, 'Record not found.')
    return redirect('manage')

@login_required
@mAdmin_only
def bulk_delete_admins(request):
    if request.method == 'POST':
        admin_ids = request.POST.getlist('admin_ids')
        if admin_ids:
            # Delete multiple admins
            deleted_count, _ = CheckLogin.objects.filter(id__in=admin_ids).delete()
            messages.success(request, f'Successfully deleted {deleted_count} record(s).')
        else:
            messages.warning(request, 'No records selected for deletion.')
    return redirect('manage')

@opAdmin_only
def OAdashboard(request):
    today = timezone.localdate()
    appointments_today = Patient.objects.filter(EntryDateandTime__date=today).count()
    admissions_pending = Patient.objects.filter(IsAdmitted=True, ExitDateandTime__isnull=True).count()
    lab_results_pending = max(Patient.objects.filter(IsAdmitted=True).count() - Patient.objects.exclude(Medication='').count(), 0)
    unread_messages = CheckLogin.objects.filter(status=False, created_by_id=request.current_actor.id).count()

    recent_patients = Patient.objects.select_related('DoctorID').order_by('-EntryDateandTime')[:6]
    operations = []
    for patient in recent_patients:
        operations.append({
            'timestamp': patient.EntryDateandTime,
            'description': f'{patient.Pname} routed to {patient.DoctorID.Dname}',
            'source': 'Patient desk',
            'level': 'warning' if patient.IsAdmitted else 'info',
        })

    recent_opadmins = CheckLogin.objects.filter(created_by_id=request.current_actor.id).order_by('-created_on')[:3]
    for admin in recent_opadmins:
        operations.append({
            'timestamp': admin.created_on,
            'description': f'{admin.username or admin.email} account reviewed',
            'source': 'Admin queue',
            'level': 'info' if admin.status else 'warning',
        })
    operations = sorted(operations, key=lambda item: item['timestamp'], reverse=True)[:7]

    chart_labels = []
    chart_data = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        chart_labels.append(day.strftime('%a'))
        chart_data.append(Patient.objects.filter(EntryDateandTime__date=day).count())

    context = {
        'appointments_today': appointments_today,
        'admissions_pending': admissions_pending,
        'lab_results_pending': lab_results_pending,
        'unread_messages': unread_messages,
        'operations': operations,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'care_summary': [
            {'label': 'Doctors available', 'value': Doctor.objects.count(), 'meta': 'Across all specialities'},
            {'label': 'Front desk staff', 'value': Receptionist.objects.count(), 'meta': 'Reception coverage'},
            {'label': 'Support helpers', 'value': Helper.objects.count(), 'meta': 'Ward assistance'},
        ],
    }
    return render(request, "Admin/OpAdmin/dashboard.html", context)

@opAdmin_only
def OAprofile(request):
    # Render Operational Admin profile including creator info
    admin_id = request.current_actor.id
    try:
        admin = CheckLogin.objects.get(id=admin_id)
    except CheckLogin.DoesNotExist:
        return clear_auth_cookies(redirect('login'))
    password_modal_open = False
    password_message = None
    password_message_level = None
    # handle profile update including avatar upload
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if form_type == 'change_password':
            password_modal_open = True

            if not current_password or not new_password or not confirm_password:
                password_message = 'Please fill in all password fields.'
                password_message_level = 'danger'
            elif not admin.check_password(current_password):
                password_message = 'Current password is incorrect.'
                password_message_level = 'danger'
            elif new_password != confirm_password:
                password_message = 'New password and confirm password do not match.'
                password_message_level = 'danger'
            elif len(new_password) < 8:
                password_message = 'New password must be at least 8 characters long.'
                password_message_level = 'danger'
            else:
                try:
                    admin.password = new_password
                    admin.save()
                    messages.success(request, 'Password changed successfully.')
                    return redirect('OAprofile')
                except Exception as e:
                    print('Error changing OA password:', str(e))
                    messages.error(request, f'Error changing password: {e}')
        else:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            gender = request.POST.get('gender')
            avatar_file = request.FILES.get('avatar')
            # Debug prints to help trace incoming data
            print('OAprofile POST data:', {'name': name, 'phone': phone, 'address': address, 'gender': gender, 'has_avatar': bool(avatar_file)})

            if name:
                admin.username = name
            if phone is not None:
                admin.phone = phone
            if address is not None:
                admin.address = address
            if gender is not None:
                admin.gender = gender
            if avatar_file:
                admin.avatar = avatar_file

            try:
                admin.save()
                # Use messages framework and PRG pattern to avoid double-post
                messages.success(request, 'Profile updated successfully.')
                return redirect('OAprofile')
            except Exception as e:
                # Log and show error message so we can diagnose upload/save problems
                print('Error saving OAprofile:', str(e))
                messages.error(request, f'Error saving profile: {e}')
                # fallthrough to render the page with error message

    creator = admin.created_by
    created_by_name = creator.username if creator and getattr(creator, 'username', None) else (creator.email if creator else 'System')
    created_on_str = admin.created_on.strftime('%Y-%m-%d %H:%M:%S') if getattr(admin, 'created_on', None) else ''

    context = {
        'admin': admin,
        'admin_username': admin.username,
        'admin_email': admin.email,
        'created_by_name': created_by_name,
        'created_on': created_on_str,
        'appointments_today': 0,
        'admissions_pending': 0,
        'unread_messages': 0,
        'recent_activities': [],
        'password_modal_open': password_modal_open,
        'password_message': password_message,
        'password_message_level': password_message_level,
    }
    return render(request, 'Admin/OpAdmin/profile.html', context)




def _get_next_id(model, pk_field):
    last_record = model.objects.order_by(f'-{pk_field}').first()
    return getattr(last_record, pk_field) + 1 if last_record else 1

def _get_next_id(model, pk_field):
    last_record = model.objects.order_by(f'-{pk_field}').first()
    return getattr(last_record, pk_field) + 1 if last_record else 1

@login_required
@opAdmin_only
def doctoradd(request):
    context = {'errors': {}, 'name': '', 'specialization': '', 'phone': '', 'email': ''}
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not name:
            context['errors']['name'] = 'Doctor name is required.'
        if not specialization:
            context['errors']['specialization'] = 'Specialization is required.'
        if not phone:
            context['errors']['phone'] = 'Phone number is required.'
        if not email:
            context['errors']['email'] = 'Email is required.'
        if not password:
            context['errors']['password'] = 'Password is required.'
        if email and Doctor.objects.filter(Email__iexact=email).exists():
            context['errors']['email'] = 'A doctor with that email already exists.'

        context.update({'name': name, 'specialization': specialization, 'phone': phone, 'email': email})

        if not context['errors']:
            try:
                Doctor.objects.create(
                    DocID=_get_next_id(Doctor, 'DocID'),
                    Dname=name,
                    Specialization=specialization,
                    Phone=phone,
                    Email=email,
                    Password=password,
                    Status=True,
                )
                messages.success(request, 'Doctor added successfully.')
                return redirect('doctormanage')
            except Exception as e:
                messages.error(request, f'Unable to add doctor: {e}')

    return render(request, 'Admin/OpAdmin/doctor/add.html', context)

@login_required
@opAdmin_only
def doctormanage(request):
    q = request.GET.get('q', '').strip()
    doctors = Doctor.objects.all()

    if request.method == 'POST':
        delete_id = request.POST.get('delete_id')
        if delete_id:
            try:
                doctor = Doctor.objects.get(DocID=delete_id)
                doctor.delete()
                messages.success(request, 'Doctor deleted successfully.')
            except Doctor.DoesNotExist:
                messages.error(request, 'Doctor not found.')
            return redirect('doctormanage')

    if q:
        doctors = doctors.filter(
            Q(Dname__icontains=q) |
            Q(Specialization__icontains=q) |
            Q(Email__icontains=q)
        )

    return render(request, 'Admin/OpAdmin/doctor/manage.html', {
        'doctors': doctors,
        'query': q,
    })

@login_required
@opAdmin_only
def helperadd(request):
    context = {'errors': {}, 'name': '', 'phone': '', 'email': ''}
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not name:
            context['errors']['name'] = 'Helper name is required.'
        if not phone:
            context['errors']['phone'] = 'Phone number is required.'
        if not email:
            context['errors']['email'] = 'Email is required.'
        if not password:
            context['errors']['password'] = 'Password is required.'
        if email and Helper.objects.filter(Email__iexact=email).exists():
            context['errors']['email'] = 'A helper with that email already exists.'

        context.update({'name': name, 'phone': phone, 'email': email})

        if not context['errors']:
            try:
                Helper.objects.create(
                    HelperID=_get_next_id(Helper, 'HelperID'),
                    Hname=name,
                    Phone=phone,
                    Email=email,
                    Password=password,
                    Status=True,
                )
                messages.success(request, 'Helper added successfully.')
                return redirect('helpermanage')
            except Exception as e:
                messages.error(request, f'Unable to add helper: {e}')

    return render(request, 'Admin/OpAdmin/helper/add.html', context)

@login_required
@opAdmin_only
def helpermanage(request):
    q = request.GET.get('q', '').strip()
    helpers = Helper.objects.all()

    if request.method == 'POST':
        delete_id = request.POST.get('delete_id')
        if delete_id:
            try:
                helper = Helper.objects.get(HelperID=delete_id)
                helper.delete()
                messages.success(request, 'Helper deleted successfully.')
            except Helper.DoesNotExist:
                messages.error(request, 'Helper not found.')
            return redirect('helpermanage')

    if q:
        helpers = helpers.filter(
            Q(Hname__icontains=q) |
            Q(Email__icontains=q) |
            Q(Phone__icontains=q)
        )

    return render(request, 'Admin/OpAdmin/helper/manage.html', {
        'helpers': helpers,
        'query': q,
    })

@login_required
@opAdmin_only
def receptionistadd(request):
    context = {'errors': {}, 'name': '', 'phone': '', 'email': ''}
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not name:
            context['errors']['name'] = 'Receptionist name is required.'
        if not phone:
            context['errors']['phone'] = 'Phone number is required.'
        if not email:
            context['errors']['email'] = 'Email is required.'
        if not password:
            context['errors']['password'] = 'Password is required.'
        if email and Receptionist.objects.filter(Email__iexact=email).exists():
            context['errors']['email'] = 'A receptionist with that email already exists.'

        context.update({'name': name, 'phone': phone, 'email': email})

        if not context['errors']:
            try:
                Receptionist.objects.create(
                    RecID=_get_next_id(Receptionist, 'RecID'),
                    Rname=name,
                    Phone=phone,
                    Email=email,
                    Password=password,
                    Status=True,
                )
                messages.success(request, 'Receptionist added successfully.')
                return redirect('receptionistmanage')
            except Exception as e:
                messages.error(request, f'Unable to add receptionist: {e}')

    return render(request, 'Admin/OpAdmin/receptionist/add.html', context)

@login_required
@opAdmin_only
def receptionistmanage(request):
    q = request.GET.get('q', '').strip()
    receptionists = Receptionist.objects.all()

    if request.method == 'POST':
        delete_id = request.POST.get('delete_id')
        if delete_id:
            try:
                receptionist = Receptionist.objects.get(RecID=delete_id)
                receptionist.delete()
                messages.success(request, 'Receptionist deleted successfully.')
            except Receptionist.DoesNotExist:
                messages.error(request, 'Receptionist not found.')
            return redirect('receptionistmanage')

    if q:
        receptionists = receptionists.filter(
            Q(Rname__icontains=q) |
            Q(Email__icontains=q) |
            Q(Phone__icontains=q)
        )

    return render(request, 'Admin/OpAdmin/receptionist/manage.html', {
        'receptionists': receptionists,
        'query': q,
    })


def logout(request):
    return clear_auth_cookies(redirect("login"))


def get_doctor_account(actor):
    if not actor or actor.user_type != 'doctor':
        return None
    return Doctor.objects.filter(DocID=actor.id).first()


def get_staff_account_by_actor(actor):
    if not actor:
        return None
    if actor.user_type == 'doctor':
        return Doctor.objects.filter(DocID=actor.id).first()
    if actor.user_type == 'receptionist':
        return Receptionist.objects.filter(RecID=actor.id).first()
    if actor.user_type == 'helper':
        return Helper.objects.filter(HelperID=actor.id).first()
    return None


@login_required
@doctor_only
def doctor_dashboard(request):
    actor = request.current_actor
    doctor = get_doctor_account(actor)
    if not doctor:
        return clear_auth_cookies(redirect('login'))

    patients = Patient.objects.filter(DoctorID=doctor)
    today = timezone.localdate()
    today_patients = patients.filter(EntryDateandTime__date=today).count()
    active_admissions = patients.filter(IsAdmitted=True, ExitDateandTime__isnull=True).count()
    follow_ups = patients.filter(Medication='').count()
    total_patients = patients.count()

    recent_patients = patients.order_by('-EntryDateandTime')[:6]
    history = []
    for patient in recent_patients:
        history.append({
            'timestamp': patient.EntryDateandTime,
            'patient': patient.Pname,
            'status': 'Admitted' if patient.IsAdmitted else 'Released',
            'source': 'Patient intake',
        })

    chart_labels = []
    chart_data = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        chart_labels.append(day.strftime('%a'))
        chart_data.append(patients.filter(EntryDateandTime__date=day).count())

    context = {
        'doctor': doctor,
        'actor': actor,
        'today_patients': today_patients,
        'active_admissions': active_admissions,
        'follow_ups': follow_ups,
        'total_patients': total_patients,
        'recent_patients': recent_patients,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'Admin/OpAdmin/doctor/dashboard.html', context)


@login_required
@doctor_only
def doctor_profile(request):
    actor = request.current_actor
    doctor = get_doctor_account(actor)
    if not doctor:
        return clear_auth_cookies(redirect('login'))

    profile_message = None
    password_message = None
    password_level = None

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'change_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not current_password or not new_password or not confirm_password:
                password_message = 'Please fill in all password fields.'
                password_level = 'danger'
            elif not doctor.check_password(current_password):
                password_message = 'Current password is incorrect.'
                password_level = 'danger'
            elif new_password != confirm_password:
                password_message = 'New passwords do not match.'
                password_level = 'danger'
            elif len(new_password) < 8:
                password_message = 'Password must be at least 8 characters long.'
                password_level = 'danger'
            else:
                doctor.Password = new_password
                try:
                    doctor.save()
                    messages.success(request, 'Password updated successfully.')
                    return redirect('doctor_profile')
                except Exception as e:
                    password_message = f'Unable to update password: {e}'
                    password_level = 'danger'
        else:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            email = request.POST.get('email')

            doctor.Dname = name or doctor.Dname
            doctor.Phone = phone or doctor.Phone
            doctor.Email = email or doctor.Email

            try:
                doctor.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('doctor_profile')
            except Exception as e:
                profile_message = f'Unable to save profile: {e}'

    context = {
        'actor': actor,
        'doctor': doctor,
        'profile_message': profile_message,
        'password_message': password_message,
        'password_level': password_level,
    }
    return render(request, 'Admin/OpAdmin/doctor/profile.html', context)


@login_required
def staff_profile(request):
    actor = request.current_actor
    account = get_staff_account_by_actor(actor)
    if not account:
        return clear_auth_cookies(redirect('login'))

    profile_message = None
    profile_level = None
    password_message = None
    password_level = None

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'change_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not current_password or not new_password or not confirm_password:
                password_message = 'Please fill in all password fields.'
                password_level = 'danger'
            elif not account.check_password(current_password):
                password_message = 'Current password is incorrect.'
                password_level = 'danger'
            elif new_password != confirm_password:
                password_message = 'New passwords do not match.'
                password_level = 'danger'
            elif len(new_password) < 8:
                password_message = 'Password must be at least 8 characters long.'
                password_level = 'danger'
            else:
                account.Password = new_password
                try:
                    account.save()
                    messages.success(request, 'Password updated successfully.')
                    return redirect('staff_profile')
                except Exception as e:
                    password_message = f'Unable to update password: {e}'
                    password_level = 'danger'
        else:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            email = request.POST.get('email')

            if actor.user_type == 'doctor':
                account.Dname = name or account.Dname
                account.Phone = phone or account.Phone
                account.Email = email or account.Email
            elif actor.user_type == 'receptionist':
                account.Rname = name or account.Rname
                account.Phone = phone or account.Phone
                account.Email = email or account.Email
            elif actor.user_type == 'helper':
                account.Hname = name or account.Hname
                account.Phone = phone or account.Phone
                account.Email = email or account.Email

            try:
                account.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('staff_profile')
            except Exception as e:
                profile_message = f'Unable to save profile: {e}'
                profile_level = 'danger'

    context = {
        'actor': actor,
        'account': account,
        'profile_message': profile_message,
        'profile_level': profile_level,
        'password_message': password_message,
        'password_level': password_level,
    }
    return render(request, 'Admin/Staff/profile.html', context)


@login_required
def staff_dashboard(request):
    actor = request.current_actor
    context = {
        'actor_name': actor.display_name,
        'actor_email': actor.email,
        'actor_role': actor.role.title(),
        'patient_count': Patient.objects.count(),
        'doctor_count': Doctor.objects.count(),
        'receptionist_count': Receptionist.objects.count(),
        'helper_count': Helper.objects.count(),
    }
    return render(request, 'Admin/Staff/dashboard.html', context)


@already_authenticated
def forgot_password(request):
    """Handle forgot password email request"""
    if request.method == 'POST':
        email = request.POST.get('email')

        user, account_type = get_account_for_password_reset(email)

        if user:
            # Delete old tokens for this email
            PasswordResetToken.objects.filter(email=email).delete()

            # Generate new reset token
            reset_token = PasswordResetToken.objects.create(email=email)

            # Create reset link
            reset_link = request.build_absolute_uri(f'/reset-password/{reset_token.token}/')

            # Send email with reset link
            try:
                send_mail(
                    subject='Password Reset Request - HCLSDB',
                    message=f"""
Hello,

We received a request to reset your password. Click the link below to create a new password:

{reset_link}

This link will expire in 24 hours.

If you didn't request a password reset, you can safely ignore this email.

Best regards,
HCLSDB Team
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending email: {str(e)}")

        # Always show success message for security (don't reveal if email exists)
        return render(request, 'Admin/Anonymous/forgot_password.html', {
            'email_sent': True
        })

    return render(request, 'Admin/Anonymous/forgot_password.html')


@already_authenticated
def reset_password(request, token):
    """Handle password reset"""
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        return render(request, 'Admin/Anonymous/reset_password.html', {
            'error': 'Invalid or expired reset link. Please request a new one.'
        })

    # Check if token is valid
    if not reset_token.is_valid():
        return render(request, 'Admin/Anonymous/reset_password.html', {
            'error': 'This reset link has expired. Please request a new one.'
        })

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validate passwords
        if not password or not confirm_password:
            return render(request, 'Admin/Anonymous/reset_password.html', {
                'error': 'Please fill in all fields.',
                'token': token
            })

        if password != confirm_password:
            return render(request, 'Admin/Anonymous/reset_password.html', {
                'error': 'Passwords do not match.',
                'token': token
            })

        if len(password) < 8:
            return render(request, 'Admin/Anonymous/reset_password.html', {
                'error': 'Password must be at least 8 characters long.',
                'token': token
            })

        # Update user password
        try:
            user, account_type = get_account_for_password_reset(reset_token.email)
            if not user:
                raise CheckLogin.DoesNotExist
            set_account_password(user, account_type, password)

            # Mark token as used
            reset_token.is_used = True
            reset_token.save()

            return render(request, 'Admin/Anonymous/reset_password.html', {
                'success': True
            })
        except CheckLogin.DoesNotExist:
            return render(request, 'Admin/Anonymous/reset_password.html', {
                'error': 'User not found.',
                'token': token
            })

    return render(request, 'Admin/Anonymous/reset_password.html', {
        'token': token
    })
