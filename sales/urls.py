from django.urls import path
from . import views

urlpatterns = [
    # 认证
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # 主要页面
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('my-customers/', views.my_customers_view, name='my_customers'),
    path('customer/add/', views.customer_detail_view, name='customer_add'),
    path('customer/<int:pk>/', views.customer_detail_view, name='customer_detail'),
    path('high-seas/', views.high_seas_view, name='high_seas'),
    path('visited/', views.visited_customers_view, name='visited'),
    path('signed/', views.signed_customers_view, name='signed'),
    path('key-customers/', views.key_customers_view, name='key_customers'),
    path('settings/', views.settings_view, name='settings'),
    
    # API endpoints
    path('api/pending-reminders/', views.get_pending_reminders_api, name='pending_reminders_api'),
]

