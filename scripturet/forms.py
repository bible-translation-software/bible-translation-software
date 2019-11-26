from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

User = get_user_model()

class ChangeNameForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        # These two lines cause the strings to be included in .po files:
        self.fields['first_name'].label = _("First name")
        self.fields['last_name'].label = _("Last name")

    class Meta:
        model = User
        fields = ['first_name', 'last_name']
