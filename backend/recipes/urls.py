from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet,
    TagViewSet,
    RecipeViewSet,
    FavoriteViewSet,
    ShoppingCartViewSet
)

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'shopping_cart', ShoppingCartViewSet,
                basename='shopping_cart')

urlpatterns = [
    path('', include(router.urls)),
]
