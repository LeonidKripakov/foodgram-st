from rest_framework import serializers
from .fields import Base64ImageField
from .models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart
)
from users.serializers import CustomUserSerializer


class RecipeSimpleSerializer(serializers.ModelSerializer):

    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipeingredient_set',
        many=True,
        read_only=True
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
        queryset=Ingredient.objects.all(),
        source='ingredient',
        write_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        ings = data.get('ingredients')
        if not ings:
            raise serializers.ValidationError(
                {'ingredients': 'Нужен хотя бы один ингредиент.'})
        seen = set()
        for ing in ings:
            amount = ing.get('amount')
            if amount is None or amount < 1:
                raise serializers.ValidationError(
                    {'amount': 'Количество должно быть ≥ 1.'})
            pk = ing['ingredient'].pk
            if pk in seen:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.')
            seen.add(pk)

        if not data.get('name', '').strip():
            raise serializers.ValidationError(
                {'name': 'Название не может быть пустым.'})
        if not data.get('text', '').strip():
            raise serializers.ValidationError(
                {'text': 'Описание не может быть пустым.'})

        # Картинка
        if 'image' not in data or data.get('image') is None:
            raise serializers.ValidationError(
                {'image': 'Картинка обязательна.'})

        # Время готовки
        ct = data.get('cooking_time')
        if ct is None or ct < 1:
            raise serializers.ValidationError(
                {'cooking_time': 'Время приготовления ≥ 1 мин.'})

        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags', [])
        validated_data.pop('author', None)
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags)
        for ing in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ing['ingredient'],
                amount=ing['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ings = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if tags is not None:
            instance.tags.set(tags)
        if ings is not None:
            instance.recipeingredient_set.all().delete()
            for ing in ings:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ing['ingredient'],
                    amount=ing['amount']
                )
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
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в избранном!')
        return data

    def create(self, validated_data):
        return Favorite.objects.create(
            user=self.context['request'].user,
            recipe=validated_data['recipe']
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('id', 'user', 'recipe')
        read_only_fields = ('user',)

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в корзине!')
        return data

    def create(self, validated_data):
        return ShoppingCart.objects.create(
            user=self.context['request'].user,
            recipe=validated_data['recipe']
        )
