from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')

        user = User.objects.filter(username=username).first()
        if user and user.check_password(password):
            return user

        user = User.objects.filter(email=username).first()
        if user and user.check_password(password):
            return user
        return None
