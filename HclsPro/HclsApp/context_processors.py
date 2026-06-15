def admin_context(request):
    """Adds authenticated actor details to template context."""
    actor = getattr(request, 'current_actor', None)
    if not actor:
        return {}

    return {
        'admin_name': actor.display_name,
        'admin_username': actor.display_name,
        'admin_email': actor.email,
        'current_role': actor.role,
    }
