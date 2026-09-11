from django import forms
from django.core.exceptions import ValidationError

from .models import Comment


class CommentForm(forms.ModelForm):
    """Hidden 'website' field acts as a honeypot — bots fill it, humans never see it."""

    website = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
        label="",
    )

    class Meta:
        model = Comment
        fields = ["name", "email", "body"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@example.com"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Your comment"}),
        }

    def clean_website(self):
        if self.cleaned_data["website"]:
            raise ValidationError("Spam detected.")
        return self.cleaned_data["website"]