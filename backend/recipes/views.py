from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .filters import RecipeFilter
from .models import (
    Ingredient,
    Tag,
    Recipe,
    Favorite,
    ShoppingCart
)
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {'name': ['istartswith']}


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/tags/ — список всех тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """
    CRUD для рецептов + actions:
    - POST/DELETE   /api/recipes/{id}/favorite/
    - POST/DELETE   /api/recipes/{id}/shopping_cart/
    - GET            /api/recipes/{id}/get-link/
    """
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter
    filterset_fields = ['tags', 'author']
    search_fields = ['name', 'author__username']

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
        out = RecipeReadSerializer(
            ser.instance,
            context={'request': request}
        )
        headers = self.get_success_headers(out.data)
        return Response(
            out.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        inst = self.get_object()
        ser = self.get_serializer(
            inst, data=request.data, partial=partial
        )
        ser.is_valid(raise_exception=True)
        self.perform_update(ser)
        out = RecipeReadSerializer(
            ser.instance,
            context={'request': request}
        )
        return Response(out.data)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if Favorite.objects.filter(user=request.user,
                                   recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже в избранном!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.create(user=request.user, recipe=recipe)
        return Response(
            FavoriteSerializer(recipe,
                               context={'request': request}
                               ).data,
            status=status.HTTP_201_CREATED
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = self.get_object()
        q = Favorite.objects.filter(user=request.user,
                                    recipe=recipe)
        if q.exists():
            q.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт не в избранном!'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if ShoppingCart.objects.filter(user=request.user,
                                       recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже в корзине!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        return Response(
            ShoppingCartSerializer(recipe,
                                   context={'request': request}
                                   ).data,
            status=status.HTTP_201_CREATED
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        q = ShoppingCart.objects.filter(user=request.user,
                                        recipe=recipe)
        if q.exists():
            q.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт не в корзине!'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[IsAuthenticatedOrReadOnly],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        url = request.build_absolute_uri(
            reverse('recipe-detail', args=[recipe.pk])
        )
        return Response({'short-link': url})


class FavoriteViewSet(mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):
    """Вьюсет для избранного пользователя."""
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ShoppingCartViewSet(mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    """Вьюсет для корзины пользователя."""
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
