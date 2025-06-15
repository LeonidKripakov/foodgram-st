from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from recipes import urls as recipes_urls
from users.views import UserViewSet
from recipes.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'ingredients', IngredientViewSet,
                basename='ingredient')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/', include('recipes.urls')),
    path('api/', include('users.urls')),
]
