from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django import forms
from django.utils.translation import ugettext_lazy as _


class CustomAuthenticationForm(AuthenticationForm):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    username = UsernameField(
        label=_("Webin-ID"),
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': True}),
    )
