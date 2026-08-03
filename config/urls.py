from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('classroom/', include('apps.classroom.urls')),
    path('quiz/', include('apps.quiz.urls')),
    path('', include('apps.accounts.urls')),
    path('classroom/', include('apps.classroom.urls')),
    path("assignment/", include("apps.assignment.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )