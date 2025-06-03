from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler403, handler404, handler500
from blog import views as blog_views
from django.contrib import admin
from django.urls import path, include

handler403 = 'pages.views.csrf_failure'
handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path(
        'auth/registration/',
        blog_views.RegistrationView.as_view(),
        name='registration'
    ),
    path('', include('blog.urls')),
    path('pages/', include('pages.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
