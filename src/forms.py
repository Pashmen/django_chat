from django import forms
from django.conf import settings


class TextAreaField(forms.CharField):
    # This custom Field is needed because after textarea tag
    # all "\n" are replaced with "\r\n"
    def clean(self, value):
        return super().clean(value.replace("\r\n", "\n"))


class MessagesForm(forms.Form):
    # Can't use forms.ModelForm because of editable=False in Model
    text = TextAreaField(
        max_length=settings.FS_MAX_MESSAGE_LENGTH,
        label=False,
        widget=forms.Textarea(attrs={'rows': 6})
    )
