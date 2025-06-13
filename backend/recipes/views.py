from rest_framework import viewsets, filters

from .models import Ingredient, Tag, Recipe
from .serializers import (
    IngredientSerializer, TagSerializer, RecipeSerializer
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра ингредиентов.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']  # Поиск по началу имени, регистронезависимо


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра тегов.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD рецептов.
    """
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
