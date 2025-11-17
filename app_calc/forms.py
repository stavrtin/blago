from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Property, Element



class SimpleUserCreationForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Логин',
            'required': 'true'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль',
            'required': 'true'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Подтверждение пароля',
            'required': 'true'
        })
    )

    class Meta:
        model = User
        fields = ('username',)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Пользователь с таким логином уже существует")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Логин',
            'required': 'true'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль',
            'required': 'true'
        })
    )


# class PropertyForm(forms.ModelForm):
#     class Meta:
#         model = Property
#         fields = ['element_id', 'property_name']
#         labels = {
#             'element_id': 'Элемент площади',
#             'property_name': 'Название характеристики'
#         }
#         widgets = {
#             'element_id': forms.Select(attrs={'class': 'form-control'}),
#             'property_name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Введите название характеристики'
#             })
#         }
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)


class PropertyForm(forms.ModelForm):
    width = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=1000,
        label='Ширина (см)',
        help_text='Только для бортового камня'
    )

    class Meta:
        model = Property
        fields = ['element_id', 'property_name']

    def clean(self):
        cleaned_data = super().clean()
        element_id = cleaned_data.get('element_id')
        width = cleaned_data.get('width')
        property_name = cleaned_data.get('property_name')

        # Проверяем, что для бортового камня указана ширина
        if element_id and 'Бортовой камень' in element_id.name_element and not width:
            raise forms.ValidationError('Для бортового камня необходимо указать ширину.')

        return cleaned_data

    # def save(self, commit=True):
    #     instance = super().save(commit=False)
    #
    #     # Если это бортовой камень и указана ширина, добавляем "ш.XXX" к названию
    #     if (instance.element_id and
    #             'Бортовой камень' in instance.element_id.name_element and
    #             self.cleaned_data.get('width')):
    #         width = self.cleaned_data['width']
    #         instance.property_name = f"{instance.property_name}"
    #
    #     if commit:
    #         instance.save()
    #     return instance
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Никаких изменений property_name - JavaScript уже всё сделал
        if commit:
            instance.save()
        return instance