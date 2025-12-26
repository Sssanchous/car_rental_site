from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from .models import Cars, Clients, Employees, Contracts


fio_validator = RegexValidator(
    regex=r'^[А-Яа-яЁё\- ]+$',
    message="ФИО может содержать только русские буквы, пробелы и дефисы"
)

phone_validator = RegexValidator(
    regex=r'^\+7\d{10}$',
    message="Телефон должен быть в формате +7XXXXXXXXXX"
)

passport_validator = RegexValidator(
    regex=r'^\d{6,10}$',
    message="Паспорт должен содержать от 6 до 10 цифр"
)

dl_validator = RegexValidator(
    regex=r'^[0-9A-Za-zА-Яа-я]{6,20}$',
    message="Номер ВУ должен содержать от 6 до 20 символов"
)

vin_validator = RegexValidator(
    regex=r'^[A-HJ-NPR-Z0-9]{17}$',
    message="VIN должен состоять из 17 символов"
)

plate_validator = RegexValidator(
    regex=r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\s?\d{2,3}$',
    message="Неверный формат госномера"
)


class CarForm(forms.ModelForm):
    plate = forms.CharField(validators=[plate_validator], widget=forms.TextInput(attrs={'class': 'form-control'}))
    vin = forms.CharField(validators=[vin_validator], widget=forms.TextInput(attrs={'class': 'form-control'}))
    brand = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    model = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    year_made = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    mileage = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Cars
        fields = [
            'plate', 'vin', 'brand', 'model',
            'year_made', 'mileage',
            'category', 'status', 'branch', 'daily_price'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'daily_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ClientForm(forms.ModelForm):
    full_name = forms.CharField(validators=[fio_validator], widget=forms.TextInput(attrs={'class': 'form-control'}))
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    passport = forms.CharField(validators=[passport_validator], widget=forms.TextInput(attrs={'class': 'form-control'}))
    dl_number = forms.CharField(validators=[dl_validator], widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(validators=[phone_validator], widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Clients
        fields = [
            'full_name', 'birth_date', 'passport',
            'dl_number', 'phone', 'email', 'address'
        ]

    def clean_passport(self):
        passport = self.cleaned_data['passport']
        qs = Clients.objects.filter(passport=passport)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Клиент с таким паспортом уже существует")
        return passport


class EmployeeForm(forms.ModelForm):
    full_name = forms.CharField(validators=[fio_validator], widget=forms.TextInput(attrs={'class': 'form-control'}))
    passport = forms.CharField(validators=[passport_validator], widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(validators=[phone_validator], widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Employees
        fields = [
            'full_name',
            'passport',
            'role',
            'branch',
            'phone',
            'email',
        ]
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].required = not bool(self.instance and self.instance.pk)

    def clean_passport(self):
        passport = self.cleaned_data['passport']
        qs = Employees.objects.filter(passport=passport)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Сотрудник с таким паспортом уже существует")
        return passport

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        qs = Employees.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Сотрудник с таким email уже существует")

        qs_u = User.objects.filter(username__iexact=email)
        if self.instance.pk:
            old_email = Employees.objects.filter(pk=self.instance.pk).values_list("email", flat=True).first()
            if old_email and old_email.lower() == email:
                qs_u = User.objects.none()
        if qs_u.exists():
            raise ValidationError("Пользователь для входа с таким email уже существует")

        return email


class ContractForm(forms.ModelForm):
    daily_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    total_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
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
            'payment': forms.Select(attrs={'class': 'form-select'}),
            'issue_branch': forms.Select(attrs={'class': 'form-select'}),
            'return_branch': forms.Select(attrs={'class': 'form-select'}),
            'created_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()

        car = cleaned.get("car")
        issue = cleaned.get("issue_date")
        ret = cleaned.get("return_date")

        if issue and ret and ret < issue:
            raise ValidationError("Дата возврата не может быть раньше даты выдачи")

        if car and issue and ret:
            days = (ret - issue).days + 1
            cleaned["daily_price"] = car.daily_price
            cleaned["total_amount"] = car.daily_price * days

        return cleaned
