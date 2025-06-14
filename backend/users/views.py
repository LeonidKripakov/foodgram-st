from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.contrib.auth import get_user_model

from .models import Subscription
from .serializers import UserSerializer

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe'
    )
    def subscribe(self, request, pk=None):
        author = self.get_object()
        user = request.user
        if user == author:
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
        serializer = self.get_serializer(author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        author = self.get_object()
        qs = Subscription.objects.filter(user=request.user, author=author)
        if not qs.exists():
            return Response(
                {'errors': 'Нет подписки!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        authors = Subscription.objects.filter(
            user=request.user
        ).values_list('author', flat=True)
        qs = User.objects.filter(pk__in=authors)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
