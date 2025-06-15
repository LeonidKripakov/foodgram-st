from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from recipes.fields import Base64ImageField
from .models import Subscription, Profile
from .pagination import CustomLimitOffsetPagination
from .serializers import (
    CustomUserCreateSerializer,
    CustomUserSerializer,
    SubscriptionSerializer
)

User = get_user_model()


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField()


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    pagination_class = CustomLimitOffsetPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe'
    )
    def subscribe(self, request, pk=None):
        """
        POST /api/users/{id}/subscribe/ — подписаться на автора
        Возвращает SubscriptionSerializer(author) с полями:
        id, username, first_name, last_name, email, is_subscribed,
        avatar, recipes_count, recipes
        """
        user = request.user
        author = self.get_object()
        if author == user:
            return Response(
                {'errors': 'Нельзя подписаться на себя!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            return Response(
                {'errors': 'Уже подписаны!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.create(user=user, author=author)
        serializer = SubscriptionSerializer(
            author,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        authors_ids = Subscription.objects.filter(
            user=request.user
        ).values_list('author', flat=True)
        qs = User.objects.filter(id__in=authors_ids)
        page = self.paginate_queryset(qs)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        author = self.get_object()
        qs = Subscription.objects.\
            filter(user=request.user, author=author)
        if not qs.exists():
            return Response(
                {'errors': 'Нет подписки!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='avatar'
    )
    def avatar(self, request, pk=None):

        user = self.get_object()
        avatar_field = getattr(getattr(user, 'profile', None), 'avatar', None)
        if not avatar_field:
            return Response({'avatar': None}, status=status.HTTP_200_OK)
        avatar_url = request.build_absolute_uri(avatar_field.url)
        return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def me(self, request):
        serializer = self.get_serializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get', 'put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def user_avatar(self, request):
        """
        GET  /api/users/me/avatar/    — вернуть {"avatar": URL или null}
        PUT  /api/users/me/avatar/    — загрузить avatar из base64
        DELETE /api/users/me/avatar/  — удалить avatar
        """
        user = request.user
        # гарантированно получаем профиль
        profile, _ = Profile.objects.get_or_create(user=user)

        # --- GET ---
        if request.method == 'GET':
            if profile.avatar and profile.avatar.name:
                url = request.build_absolute_uri(profile.avatar.url)
            else:
                url = None
            return Response({'avatar': url}, status=status.HTTP_200_OK)

        # --- PUT ---
        if request.method == 'PUT':
            ser = AvatarSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            avatar_file = ser.validated_data['avatar']
            # сохраняем через .save(), чтобы у FieldFile появился .url
            profile.avatar.save(avatar_file.name, avatar_file, save=True)
            full_url = request.build_absolute_uri(profile.avatar.url)
            return Response({'avatar': full_url}, status=status.HTTP_200_OK)

        # --- DELETE ---
        profile.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password'
    )
    def set_password(self, request):
        """
        POST /api/users/set_password/
        {
          "current_password": "...",
          "new_password":     "..."
        }
        """
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        cur = serializer.validated_data['current_password']
        new = serializer.validated_data['new_password']

        if not user.check_password(cur):
            return Response(
                {'current_password': 'Неверный пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
