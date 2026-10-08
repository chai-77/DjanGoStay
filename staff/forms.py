# staff/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Staff


class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = [
            'first_name',
            'last_name',
            'phone_number',
            'role',
            'salary',
            'date_of_joining',
        ]

        widgets = {
            'date_of_joining': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }

    def clean_salary(self):
        salary = self.cleaned_data['salary']
        if salary < 0:
            raise forms.ValidationError('Salary cannot be negative.')
        return salary


class StaffCreateForm(StaffForm):
    username = forms.CharField(max_length=150)
    password1 = forms.CharField(
        label='Initial password',
        strip=False,
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label='Confirm password',
        strip=False,
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields([
            'first_name',
            'last_name',
            'phone_number',
            'role',
            'salary',
            'date_of_joining',
            'username',
            'password1',
            'password2',
        ])

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already in use.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'The passwords do not match.')
        elif password1:
            user = User(username=cleaned_data.get('username', ''))
            try:
                validate_password(password1, user=user)
            except ValidationError as exc:
                self.add_error('password1', exc)

        return cleaned_data
