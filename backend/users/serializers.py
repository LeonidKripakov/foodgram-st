from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

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
                'Введите правильный username. '
                'Разрешены буквы, цифры и символы @/./+/-/_'
            )
        }
    )
    first_name = serializers.CharField(
        required=True,
        max_length=150
    )
    last_name = serializers.CharField(
        required=True,
        max_length=150
    )
    password = serializers.CharField(
        write_only=True,
        required=True
    )

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
        # Метод create_user автоматически хеширует пароль
        return User.objects.create_user(**validated_data)


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name'
        )
        read_only_fields = fields
