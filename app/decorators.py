from functools import wraps
from django.shortcuts import redirect


def member_required(f):
    @wraps(f)
    def decorator(request, *args, **kwargs):
        if hasattr(request.user, 'oh_member'):
            return f(request, *args, **kwargs)
        else:
            return redirect('authorize')
    return decorator


def admin_required(f):
    @wraps(f)
    def decorator(request, *args, **kwargs):
        if request.user.is_superuser:
            return f(request, *args, **kwargs)
        else:
            return redirect('admin_login')
    return decorator
