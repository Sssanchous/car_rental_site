from django.contrib import admin
from .models import Clients, Cars, Employees, Contracts, Maintenance

admin.site.register(Clients)
admin.site.register(Cars)
admin.site.register(Employees)
admin.site.register(Contracts)
admin.site.register(Maintenance)
