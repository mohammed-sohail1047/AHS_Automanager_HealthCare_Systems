from django.shortcuts import redirect
from functools import wraps
from HclsWebApi.authentication import get_dashboard_route_for_role


def normalize_admin_type(admin_type):
    """Convert admin_type to standard format (handles both int and string)"""
    if admin_type is None:
        return None
    
    admin_type_str = str(admin_type).strip().upper()
    
    # Handle database values
    if admin_type_str == "MADMIN" or admin_type_str == "1" or admin_type_str == "MANAGER ADMIN":
        return "MADMIN"
    elif admin_type_str == "OPADMIN" or admin_type_str == "2" or admin_type_str == "OPERATOR ADMIN":
        return "OPADMIN"
    
    return admin_type  # Return original if doesn't match


def login_required(view_func):
    """Decorator to check if user is logged in"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(request, 'current_actor', None):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def already_authenticated(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        actor = getattr(request, 'current_actor', None)
        if actor:
            return redirect(get_dashboard_route_for_role(actor.role))
        
        return view_func(request, *args, **kwargs)
    return wrapper


def mAdmin_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        actor = getattr(request, 'current_actor', None)
        if not actor:
            return redirect('login')

        admin_type = normalize_admin_type(actor.role)
        
        if admin_type != "MADMIN":
            return redirect(get_dashboard_route_for_role(admin_type))

        return view_func(request, *args, **kwargs)

    return wrapper


def opAdmin_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        actor = getattr(request, 'current_actor', None)
        if not actor:
            return redirect('login')

        admin_type = normalize_admin_type(actor.role)
        
        if admin_type != "OPADMIN":
            return redirect(get_dashboard_route_for_role(admin_type))

        return view_func(request, *args, **kwargs)

    return wrapper


def doctor_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        actor = getattr(request, 'current_actor', None)
        if not actor:
            return redirect('login')

        if str(actor.role).strip().upper() != "DOCTOR":
            return redirect(get_dashboard_route_for_role(actor.role))

        return view_func(request, *args, **kwargs)

    return wrapper

