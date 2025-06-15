from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from quiz.views import landing_page # Import your landing page view

urlpatterns = [
    path('admin/', admin.site.urls), # Default Django admin
    path('', landing_page, name='landing_page'), # Landing page at root
    path('quiz/', include('quiz.urls')), # Include quiz app urls
    path('accounts/', include('django.contrib.auth.urls')), # Include Django auth urls (login, logout, password reset)
    path('accounts/signup/', include('quiz.urls')), # Include your custom signup url
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)