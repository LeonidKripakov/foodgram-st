from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from users.views import UserViewSet
from recipes.views import IngredientViewSet, TagViewSet, RecipeViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    # Раздача медиа-файлов
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    # Раздача статики (для админки и фронтенда в DEBUG)
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
