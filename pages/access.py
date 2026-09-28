from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def allowed(user, model, action='view'):
    if not user.is_active or not user.is_staff:
        return False
    if user.is_superuser:
        return True
    if model._meta.model_name in ['accessrole', 'user', 'integrationsetting', 'apikeycredential', 'backuprecord', 'globalsetting']:
        return False
    code = f'{model._meta.app_label}.{action}_{model._meta.model_name}'
    if user.has_perm(code):
        return True
    if not hasattr(user, '_dashboard_permissions'):
        user._dashboard_permissions = set()
        for role in user.dashboard_roles.filter(is_active=True):
            user._dashboard_permissions.update(role.permissions.split())
    return code in user._dashboard_permissions


def require_permission(user, model, action='view'):
    if not allowed(user, model, action):
        raise PermissionDenied


def staff_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def audit(user, action, obj, **metadata):
    import json
    from .models import AuditLog
    AuditLog.objects.create(actor=user.get_username(), action=action, model_name=obj._meta.label,
                            object_repr=str(obj)[:260], metadata=json.dumps({'id': obj.pk, **metadata}, default=str))
