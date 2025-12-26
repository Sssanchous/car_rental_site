from django.db import models
from django.contrib.postgres.fields import DateRangeField

class Branches(models.Model):
    branch_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=120)
    address = models.CharField(max_length=200)
    contacts = models.CharField(max_length=120)

    class Meta:
        managed = False
        db_table = 'branches'

    def __str__(self):
        return self.name


class CarCategories(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=60)

    class Meta:
        managed = False
        db_table = 'car_categories'

    def __str__(self):
        return self.name


class CarStatuses(models.Model):
    status_id = models.AutoField(primary_key=True)
    status = models.CharField(unique=True, max_length=40)

    class Meta:
        managed = False
        db_table = 'car_statuses'

    def __str__(self):
        return self.status


class Cars(models.Model):
    car_id = models.AutoField(primary_key=True)
    plate = models.CharField(unique=True, max_length=12)
    vin = models.CharField(unique=True, max_length=17)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year_made = models.SmallIntegerField()
    mileage = models.IntegerField()
    category = models.ForeignKey(CarCategories, models.DO_NOTHING)
    status = models.ForeignKey(CarStatuses, models.DO_NOTHING)
    branch = models.ForeignKey(Branches, models.DO_NOTHING)
    daily_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'cars'

    def __str__(self):
        return f"{self.plate} — {self.brand} {self.model}"


class Roles(models.Model):
    role_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=60)

    class Meta:
        managed = False
        db_table = 'roles'

    def __str__(self):
        return self.name


class Clients(models.Model):
    client_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField()
    passport = models.CharField(unique=True, max_length=20)
    dl_number = models.CharField(max_length=30)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'clients'

    def __str__(self):
        return f"{self.full_name} ({self.phone})"


class ContractStatuses(models.Model):
    cstatus_id = models.AutoField(primary_key=True)
    status = models.CharField(unique=True, max_length=40)

    class Meta:
        managed = False
        db_table = 'contract_statuses'

    def __str__(self):
        return self.status


class Contracts(models.Model):
    contract_id = models.AutoField(primary_key=True)
    cstatus = models.ForeignKey(ContractStatuses, models.DO_NOTHING)
    client = models.ForeignKey(Clients, models.DO_NOTHING)
    car = models.ForeignKey(Cars, models.DO_NOTHING)
    created_at = models.DateField()
    issue_date = models.DateField()
    return_date = models.DateField()
    payment = models.CharField(max_length=12)
    issue_branch = models.ForeignKey(Branches, models.DO_NOTHING)
    return_branch = models.ForeignKey(Branches, models.DO_NOTHING, related_name='contracts_return_branch_set')
    rent_period = DateRangeField(blank=True, null=True)
    daily_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'contracts'

    def __str__(self):
        return f"Договор №{self.contract_id} — {self.client.full_name}"



class Employees(models.Model):
    employee_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    passport = models.CharField(unique=True, max_length=20)
    role = models.ForeignKey(Roles, models.DO_NOTHING)
    branch = models.ForeignKey(Branches, models.DO_NOTHING)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'employees'

    def __str__(self):
        return f"{self.full_name} — {self.role.name}"


class Maintenance(models.Model):
    maintenance_id = models.AutoField(primary_key=True)
    car = models.ForeignKey(Cars, models.DO_NOTHING)
    employee = models.ForeignKey(Employees, models.DO_NOTHING)
    service_type = models.CharField(max_length=20)
    service_date = models.DateField()
    mileage_at = models.IntegerField()
    notes = models.CharField(max_length=500)

    class Meta:
        managed = False
        db_table = 'maintenance'

    def __str__(self):
        return f"ТО #{self.maintenance_id} — {self.car.plate}"
