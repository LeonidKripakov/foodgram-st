from django.http import HttpResponse
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)

from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import serializers
from .filters import RecipeFilter
from .models import Ingredient, Tag, Recipe, Favorite, ShoppingCart
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer
)


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ['name']


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {'name': ['istartswith']}
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter
    search_fields = ['name', 'author__username']

    def get_queryset(self):
    
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            # Фильтр избранного
            fav = self.request.query_params.get('is_favorited')
            if fav in ('true', 'True', '1'):
                queryset = queryset.filter(favorited_by__user=user)
            # Фильтр корзины
            cart = self.request.query_params.get('is_in_shopping_cart')
            if cart in ('true', 'True', '1'):
                queryset = queryset.filter(in_shopping_carts__user=user)
        return queryset


    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        self.perform_create(ser)
        out = RecipeReadSerializer(ser.instance, context={'request': request})
        return Response(
            out.data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(out.data)
        )

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        partial = kwargs.pop('partial', False)
        ser = self.get_serializer(recipe, data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        self.perform_update(ser)
        out = RecipeReadSerializer(ser.instance, context={'request': request})
        return Response(out.data)

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже в избранном!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.create(user=request.user, recipe=recipe)
        data = RecipeSimpleSerializer(
            recipe, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = self.get_object()
        qs = Favorite.objects.filter(user=request.user, recipe=recipe)
        if qs.exists():
            qs.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт не в избранном!'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже в корзине!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        data = RecipeSimpleSerializer(recipe, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        qs = ShoppingCart.objects.filter(user=request.user, recipe=recipe)
        if qs.exists():
            qs.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт не в корзине!'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """
        GET /api/recipes/download_shopping_cart/
        Текстовый список ингредиентов по всем рецептам в корзине.
        """
        ingredients = {}
        recipes = Recipe.objects.filter(in_shopping_carts__user=request.user)
        for rec in recipes:
            for ri in rec.recipeingredient_set.all():
                key = (ri.ingredient.name, ri.ingredient.measurement_unit)
                ingredients[key] = ingredients.get(key, 0) + ri.amount

        lines = [
            f"{name} ({unit}) — {amt}" for (name, unit),
            amt in ingredients.items()]
        content = "\n".join(lines)
        resp = HttpResponse(content, content_type='text/plain')
        resp['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return resp

    @action(detail=True, methods=['get'],
            permission_classes=[IsAuthenticatedOrReadOnly], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        url = request.build_absolute_uri(reverse('recipe-detail', args=[recipe.pk]))
        return Response({'short-link': url})


class ShoppingCartViewSet(mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    serializer_class = ShoppingCartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ShoppingCart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def download(self, request):
        ingredients = {}
        recipes = Recipe.objects.filter(
            in_shopping_carts__user=request.user
        )
        for recipe in recipes:
            for ri in recipe.recipeingredient_set.all():
                key = (
                    ri.ingredient.name,
                    ri.ingredient.measurement_unit
                )
                ingredients[key] = ingredients.get(key, 0) + ri.amount

        lines = [
            f"{name} ({unit}) — {amt}"
            for (name, unit), amt in ingredients.items()
        ]
        content = "\n".join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


class RecipeSimpleSerializer(serializers.ModelSerializer):
    """
    Мини-сериализатор рецепта для включения в подписки:
    возвращает только id, name, image, cooking_time
    """
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
