from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import Subscription

User = get_user_model()


class CustomUserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+\Z',
        max_length=150,
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
        error_messages={
            'invalid': (
                'Введите корректный username: '
                'буквы, цифры и символы @/./+/-/_'
            )
        }
    )
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()

    def get_avatar(self, obj):
        request = self.context.get('request')
        avatar = getattr(getattr(obj, 'profile', None), 'avatar', None)
        if not avatar or not avatar.name:
            return None
        url = avatar.url
        return request.build_absolute_uri(url) if request else url


class SubscriptionSerializer(CustomUserSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )

    def get_recipes(self, author):
        from recipes.serializers import RecipeSimpleSerializer
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        qs = author.recipes.all()
        if limit and limit.isdigit():
            qs = qs[: int(limit)]
        return RecipeSimpleSerializer(
            qs, many=True, context=self.context
        ).data

    def get_recipes_count(self, author):
        return author.recipes.count()
