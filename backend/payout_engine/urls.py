"""
URL configuration for payout_engine project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("""
        <div style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #2563eb;">Playto Pay Engine</h1>
            <p style="color: #4b5563;">Status: <span style="color: #10b981; font-weight: bold;">SYSTEM ACTIVE</span></p>
            <p>The backend payout processing engine is running correctly.</p>
            <hr style="width: 200px; margin: 20px auto; border-color: #e5e7eb;">
            <p style="font-size: 0.9rem;">
                <a href="/admin/" style="color: #2563eb; text-decoration: none;">Admin Panel</a> | 
                <a href="/api/v1/merchants/" style="color: #2563eb; text-decoration: none;">API Access</a>
            </p>
        </div>
    """)

urlpatterns = [
    path('', home_view),
    path('admin/', admin.site.urls),
    path('api/v1/', include('payouts.urls')),
]
