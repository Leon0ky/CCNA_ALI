from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import necessary views and forms for authentication customization
from django.contrib.auth.views import LoginView # Import Django's default LoginView
from quiz.forms import CustomAuthenticationForm # Import your custom form
from quiz.views import landing_page, signup_view # Import your landing page view and custom signup_view

urlpatterns = [
    path('admin/', admin.site.urls), # Default Django admin
    path('', landing_page, name='landing_page'), # Landing page at root

    # --- Authentication URLs ---
    # Use your custom signup view directly
    path('accounts/signup/', signup_view, name='signup'),
    # Override Django's default login view to use your custom form
    path('accounts/login/', LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=CustomAuthenticationForm
    ), name='login'),
    # Include Django's default auth URLs for logout, password reset, etc.
    # Note: The specific 'login' URL above will take precedence over the one in auth.urls
    path('accounts/', include('django.contrib.auth.urls')),
    # --- END Authentication URLs ---

    # Include quiz app urls (this maps quiz.urls to /quiz/ prefix)
    path('quiz/', include('quiz.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)