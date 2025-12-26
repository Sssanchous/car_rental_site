from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

from .models import Cars, Clients, Employees, Contracts
import re


fio_validator = RegexValidator(
    regex=r'^[А-Яа-яЁё\- ]+$',
    message="ФИО может содержать только русские буквы, пробелы и дефисы."
)

phone_validator = RegexValidator(
    regex=r'^\+7\d{10}$',
    message="Телефон должен быть в формате +7XXXXXXXXXX (10 цифр)."
)

passport_validator = RegexValidator(
    regex=r'^\d{6,10}$',
    message="Паспорт должен содержать от 6 до 10 цифр."
)

dl_validator = RegexValidator(
    regex=r'^[0-9A-Za-zА-Яа-я]{6,20}$',
    message="Номер ВУ должен содержать от 6 до 20 символов (буквы/цифры)."
)

vin_validator = RegexValidator(
    regex=r'^[A-HJ-NPR-Z0-9]{17}$',
    message="VIN должен состоять из 17 символов (латинские буквы и цифры, без I, O, Q)."
)

plate_validator = RegexValidator(
    regex=r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\s?\d{2,3}$',
    message="Госномер должен быть вида А123БВ 77 / А123БВ 777 (только разрешённые буквы)."
)


class CarForm(forms.ModelForm):
    plate = forms.CharField(
        validators=[plate_validator],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    vin = forms.CharField(
        validators=[vin_validator],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    brand = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    model = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    year_made = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    mileage = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Cars
        fields = [
            'plate', 'vin', 'brand', 'model', 'year_made',
            'mileage', 'category', 'status', 'branch', 'daily_price'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'daily_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ClientForm(forms.ModelForm):
    full_name = forms.CharField(
        validators=[fio_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иванов Иван Иванович'
        })
    )

    birth_date = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'placeholder': 'ГГГГ-ММ-ДД',
            'type': 'date'
        })
    )

    passport = forms.CharField(
        validators=[passport_validator],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    dl_number = forms.CharField(
        validators=[dl_validator],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    phone = forms.CharField(
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7XXXXXXXXXX'
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    address = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Clients
        fields = [
            'full_name', 'birth_date', 'passport', 'dl_number',
            'phone', 'email', 'address'
        ]


class EmployeeForm(forms.ModelForm):
    full_name = forms.CharField(
        validators=[fio_validator],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    passport = forms.CharField(
        validators=[passport_validator],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    phone = forms.CharField(
        validators=[phone_validator],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Employees
        fields = ['full_name', 'passport', 'role', 'branch', 'phone', 'email']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
        }


class ContractForm(forms.ModelForm):
    created_at = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    issue_date = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    return_date = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    PAYMENT_CHOICES = [
        ('наличный', 'Наличный'),
        ('безналичный', 'Безналичный'),
    ]

    payment = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Contracts
        fields = [
            'cstatus',
            'client',
            'car',
            'created_at',
            'issue_date',
            'return_date',
            'payment',
            'issue_branch',
            'return_branch',
            'daily_price',
            'total_amount'
        ]
        widgets = {
            'cstatus': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'car': forms.Select(attrs={'class': 'form-select'}),
            'issue_branch': forms.Select(attrs={'class': 'form-select'}),
            'return_branch': forms.Select(attrs={'class': 'form-select'}),
            'daily_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        issue = cleaned.get("issue_date")
        ret = cleaned.get("return_date")

        if issue and ret and ret < issue:
            raise ValidationError("Дата возврата не может быть раньше даты выдачи.")

        return cleaned
