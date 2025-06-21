from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

COOKING_TIME_MIN = 1
COOKING_TIME_MAX = 32_000
AMOUNT_MIN = 1
AMOUNT_MAX = 32_000


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Название"
    )
    measurement_unit = models.CharField(
        max_length=50,
        verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name="Автор"
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Название"
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name="Картинка"
    )
    text = models.TextField(
        verbose_name="Описание"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name="Ингредиенты"
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления (мин)",
        validators=[
            MinValueValidator(COOKING_TIME_MIN),
            MaxValueValidator(COOKING_TIME_MAX),
        ]
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ['-id']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(AMOUNT_MIN),
            MaxValueValidator(AMOUNT_MAX),
        ]
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецепте"
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]
        ordering = ['id']

    def __str__(self):
        return (
            f"{self.ingredient.name} — {self.amount} "
            f"({self.ingredient.measurement_unit})"
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'recipe')
        ordering = ['id']

    def __str__(self):
        return f"{self.user} — {self.recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_carts'
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'
        unique_together = ('user', 'recipe')
        ordering = ['id']

    def __str__(self):
        return f"{self.user} — {self.recipe}"
