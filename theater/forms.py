from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(required=False, label="Имя")
    last_name = forms.CharField(required=False, label="Фамилия")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем стили Tailwind/TW-like для инпутов
        for name, field in self.fields.items():
            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (
                f"{existing_classes} w-full px-4 py-3 border border-gray-200 rounded-lg bg-white input-elevated focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/30 transition"
            ).strip()
        self.fields["username"].widget.attrs.setdefault("placeholder", "Логин")
        self.fields["email"].widget.attrs.setdefault("placeholder", "example@mail.com")
        self.fields["first_name"].widget.attrs.setdefault("placeholder", "Имя")
        self.fields["last_name"].widget.attrs.setdefault("placeholder", "Фамилия")
        self.fields["password1"].widget.attrs.setdefault("class", "w-full px-4 py-2 border rounded focus:outline-none focus:border-brand")
        self.fields["password1"].widget.attrs.setdefault("placeholder", "Пароль")
        self.fields["password2"].widget.attrs.setdefault("class", "w-full px-4 py-2 border rounded focus:outline-none focus:border-brand")
        self.fields["password2"].widget.attrs.setdefault("placeholder", "Подтверждение пароля")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

