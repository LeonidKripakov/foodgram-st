from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from recipes.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet
)

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('djoser.urls')),             
    path('api/auth/', include('djoser.urls.authtoken')), 
    path('api/', include(router.urls)),
]