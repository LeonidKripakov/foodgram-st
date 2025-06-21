from io import BytesIO

import django_filters
from django.db.models import Sum
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import LimitOffsetPagination

from .filters import RecipeFilter
from .models import (
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    RecipeIngredient
)
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    RecipeSimpleSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer
)


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name', lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ['name']


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LimitOffsetPagination
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter
    ]
    filterset_class = RecipeFilter
    search_fields = ['name', 'author__username']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            fav = self.request.query_params.get('is_favorited')
            if fav in ('true', 'True', '1'):
                queryset = queryset.filter(favorited_by__user=user)
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output = RecipeReadSerializer(
            serializer.instance, context={'request': request}
        )
        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(output.data)
        )

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(
            recipe, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        output = RecipeReadSerializer(
            serializer.instance, context={'request': request}
        )
        return Response(output.data)

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if recipe.favorited_by.filter(user=request.user).exists():
            return Response(
                {'errors': 'Рецепт уже в избранном!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe.favorited_by.create(user=request.user)
        data = RecipeSimpleSerializer(
            recipe, context={'request': request}
        ).data
        return Response(data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = self.get_object()
        qs = recipe.favorited_by.filter(user=request.user)
        if qs.exists():
            qs.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт не в избранном!'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if recipe.in_shopping_carts.filter(user=request.user).exists():
            return Response(
                {'errors': 'Рецепт уже в корзине!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe.in_shopping_carts.create(user=request.user)
        data = RecipeSimpleSerializer(
            recipe, context={'request': request}
        ).data
        return Response(data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        qs = recipe.in_shopping_carts.filter(user=request.user)
        if qs.exists():
            qs.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт не в корзине!'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        """
        GET /api/recipes/download_shopping_cart/
        Скачивание списка ингредиентов: txt и pdf.
        """
        qs = RecipeIngredient.objects.filter(
            recipe__in_shopping_carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        # Текстовый ответ
        lines = [
            f"{item['ingredient__name']} "
            f"({item['ingredient__measurement_unit']}) — "
            f"{item['total_amount']}"
            for item in qs
        ]
        text_content = "\n".join(lines)

        # PDF ответ
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        y = 800
        for line in lines:
            pdf.drawString(50, y, line)
            y -= 15
            if y < 50:
                pdf.showPage()
                y = 800
        pdf.save()
        pdf_content = buffer.getvalue()
        buffer.close()

        # Выбор формата по параметру?
        fmt = request.query_params.get('format')
        if fmt == 'pdf':
            response = HttpResponse(
                pdf_content, content_type='application/pdf'
            )
            response['Content-Disposition'] = (
                'attachment; filename="shopping_list.pdf"'
            )
        else:
            response = HttpResponse(
                text_content, content_type='text/plain'
            )
            response['Content-Disposition'] = (
                'attachment; filename="shopping_list.txt"'
            )
        return response

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


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
