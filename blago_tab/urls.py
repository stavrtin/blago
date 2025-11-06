"""
URL configuration for proj_access project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
# from app_calc.views_calc import logout, login_view  # импорт функции logout


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('app_calc.url_calc')),  # Подключаем маршруты приложения
    # path('my_app_smp/', include('my_app_smp.url_smp')),
    # path('logout/', logout, name='logout'),
    # path('login/', login_view, name='login'),  # Предполагается, что у вас есть представление для входа

]

## Добавьте это для обслуживания медиафайлов при DEBUG=False
if not settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
