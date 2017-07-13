from django.contrib.auth.models import User


class FakeEMGBackend(object):

    supports_anonymous_user = False
    supports_object_permissions = False

    def authenticate(self, request, username=None, password=None):
        user, created = User.objects.get_or_create(
            username__iexact=username,
            defaults={'username': username.lower()}
        )
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
