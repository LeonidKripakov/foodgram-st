# recipes/filters.py

import django_filters

from .models import Recipe


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_in_shopping_cart'
    )
    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )

    class Meta:
        model = Recipe
        fields = [
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        ]

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset
        if value:
            return queryset.filter(favorited_by__user=user)
        # при false — исключаем
        return queryset.exclude(favorited_by__user=user)

    def filter_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset
        if value:
            return queryset.filter(in_shopping_carts__user=user)
        # при false — исключаем
        return queryset.exclude(in_shopping_carts__user=user)
