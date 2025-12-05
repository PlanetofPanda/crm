from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(function):
    """仅管理员可访问的装饰器"""
    @wraps(function)
    @login_required
    def wrap(request, *args, **kwargs):
        if request.user.is_superuser:
            return function(request, *args, **kwargs)
        else:
            messages.error(request, '您没有权限访问此页面,仅管理员可访问。')
            return redirect('dashboard')
    return wrap


def sales_required(function):
    """销售人员可访问的装饰器"""
    @wraps(function)
    @login_required
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated:
            return function(request, *args, **kwargs)
        else:
            return redirect('login')
    return wrap
