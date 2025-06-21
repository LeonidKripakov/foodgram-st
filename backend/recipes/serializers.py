from django.contrib.auth import get_user_model
from rest_framework import serializers

from .fields import Base64ImageField
from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
    COOKING_TIME_MIN,
    COOKING_TIME_MAX,
    AMOUNT_MIN,
    AMOUNT_MAX,
)

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed', 'avatar'
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.subscriptions.filter(author=obj).exists()

    def get_avatar(self, obj):
        request = self.context.get('request')
        avatar = getattr(getattr(obj, 'profile', None), 'avatar', None)
        if not avatar or not avatar.name:
            return None
        url = avatar.url
        return request.build_absolute_uri(url) if request else url


class RecipeSimpleSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipeingredient_set', many=True, read_only=True
    )
    image = serializers.ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.favorited_by.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.in_shopping_carts.filter(user=user).exists()
        )


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient', write_only=True
    )
    amount = serializers.IntegerField(
        min_value=AMOUNT_MIN, max_value=AMOUNT_MAX, write_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    ingredients = RecipeIngredientWriteSerializer(many=True)
    cooking_time = serializers.IntegerField(
        min_value=COOKING_TIME_MIN, max_value=COOKING_TIME_MAX
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'image', 'name', 'text', 'cooking_time'
        )

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужен хотя бы один ингредиент.'}
            )
        seen = set()
        for ing in ingredients:
            pk = ing['ingredient'].pk
            if pk in seen:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.'
                )
            seen.add(pk)
        if not data.get('name', '').strip():
            raise serializers.ValidationError(
                {'name': 'Название не может быть пустым.'}
            )
        if not data.get('text', '').strip():
            raise serializers.ValidationError(
                {'text': 'Описание не может быть пустым.'}
            )
        if 'image' not in data or data.get('image') is None:
            raise serializers.ValidationError(
                {'image': 'Картинка обязательна.'}
            )
        return data

    def _save_ingredients(self, recipe, ingredients):
        for ing in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ing['ingredient'],
                amount=ing['amount']
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        author = validated_data.pop('author', self.context['request'].user)
        recipe = Recipe.objects.create(
            author=author, **validated_data
        )
        self._save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if ingredients is not None:
            instance.recipeingredient_set.all().delete()
            self._save_ingredients(instance, ingredients)
        instance.save()
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe')
        read_only_fields = ('user',)

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']
        if user.favorites.filter(recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в избранном!')
        return data

    def create(self, validated_data):
        return Favorite.objects.create(
            user=self.context['request'].user, recipe=validated_data['recipe']
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipe')
        read_only_fields = ('user',)

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']
        if user.shopping_cart.filter(recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в корзине!')
        return data

    def create(self, validated_data):
        return ShoppingCart.objects.create(
            user=self.context['request'].user, recipe=validated_data['recipe']
        )
