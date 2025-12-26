from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum, Count, Avg
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.db import models
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings
import threading
import os
import io
import json
from django.utils.timezone import now
from .models import Clients, Cars, Contracts, Employees
from .forms import CarForm, ClientForm, ContractForm, EmployeeForm
from django.db import models, IntegrityError


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        employee = Employees.objects.filter(email=email).first()
        if not employee:
            return render(request, "login.html", {"error": "Неверный логин или пароль"})

        user, created = User.objects.get_or_create(
            username=employee.email,
            defaults={"email": employee.email}
        )

        if created:
            user.set_password("12345")
            user.save()

        user = authenticate(request, username=employee.email, password=password)
        if not user:
            return render(request, "login.html", {"error": "Неверный логин или пароль"})

        login(request, user)
        next_url = request.GET.get("next") or "/clients/"
        return redirect(next_url)

    return render(request, "login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def car_list(request):
    search = request.GET.get("search", "")
    cars = Cars.objects.all()
    if search:
        cars = cars.filter(
            Q(plate__icontains=search) |
            Q(vin__icontains=search) |
            Q(brand__icontains=search) |
            Q(model__icontains=search)
        )
    return render(request, "cars/car_list.html", {"cars": cars, "search": search})


@login_required
def car_add(request):
    form = CarForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
                return redirect("car_list")
            except IntegrityError:
                form.add_error(None, "Ошибка сохранения в базе. Проверьте уникальность VIN и гос. номера.")
    return render(request, "cars/car_form.html", {"form": form, "title": "Добавить авто"})



@login_required
def car_edit(request, pk):
    car = get_object_or_404(Cars, pk=pk)
    form = CarForm(request.POST or None, instance=car)

    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
                return redirect("car_list")
            except IntegrityError:
                form.add_error(None, "Ошибка. VIN или гос. номер нарушают ограничения.")
    
    return render(request, "cars/car_form.html", {
        "form": form,
        "title": "Редактировать авто"
    })



@login_required
def car_delete(request, pk):
    get_object_or_404(Cars, pk=pk).delete()
    return redirect("car_list")


@login_required
def client_list(request):
    search = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "")

    clients = Clients.objects.all()
    if search:
        clients = clients.filter(
            Q(full_name__icontains=search) |
            Q(passport__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
    if sort == "name_asc":
        clients = clients.order_by("full_name")
    elif sort == "name_desc":
        clients = clients.order_by("-full_name")

    return render(request, "clients/client_list.html", {
        "clients": clients,
        "search": search,
        "sort": sort,
        "title": "Клиенты"
    })





@login_required
def client_add(request):
    form = ClientForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
                return redirect("client_list")
            except IntegrityError:
                form.add_error(None, "Ошибка сохранения в базе. Проверьте, что паспорт, телефон и email не дублируются.")
    return render(request, "clients/client_form.html", {"form": form, "title": "Добавить клиента"})



@login_required
def client_edit(request, pk):
    client = get_object_or_404(Clients, pk=pk)
    form = ClientForm(request.POST or None, instance=client)

    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
                return redirect("client_list")
            except IntegrityError:
                form.add_error(None, "Ошибка БД. Телефон, паспорт или email нарушают ограничения.")
    
    return render(request, "clients/client_form.html", {
        "form": form,
        "title": "Редактировать клиента"
    })

@login_required
def client_delete(request, pk):
    get_object_or_404(Clients, pk=pk).delete()
    return redirect("client_list")


@login_required
def contract_list(request):
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "")

    contracts = Contracts.objects.select_related("client", "car")

    if search:
        contracts = contracts.filter(
            Q(client__full_name__icontains=search) |
            Q(car__plate__icontains=search)
        )

    if sort == "issue_asc":
        contracts = contracts.order_by("issue_date")
    elif sort == "issue_desc":
        contracts = contracts.order_by("-issue_date")

    return render(request, "contracts/contract_list.html", {
        "contracts": contracts,
        "search": search,
        "sort": sort,
    })



@login_required
def contract_add(request):
    form = ContractForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("contract_list")
    return render(request, "contracts/contract_form.html", {"form": form, "title": "Добавить договор"})


@login_required
def contract_edit(request, pk):
    contract = get_object_or_404(Contracts, pk=pk)
    form = ContractForm(request.POST or None, instance=contract)

    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
                return redirect("contract_list")
            except IntegrityError:
                form.add_error(None, "Ошибка БД. Проверьте даты и статус договора.")
    
    return render(request, "contracts/contract_form.html", {
        "form": form,
        "title": "Редактировать договор"
    })



@login_required
def contract_delete(request, pk):
    get_object_or_404(Contracts, pk=pk).delete()
    return redirect("contract_list")


@login_required
def employee_list(request):
    search = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "")

    employees = Employees.objects.select_related("role", "branch")

    if search:
        employees = employees.filter(
            Q(full_name__icontains=search) |
            Q(passport__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(role__name__icontains=search) |
            Q(branch__name__icontains=search)
        )

    if sort == "name_asc":
        employees = employees.order_by("full_name")
    elif sort == "name_desc":
        employees = employees.order_by("-full_name")

    return render(request, "employees/employee_list.html", {
        "employees": employees,
        "search": search,
        "sort": sort,
        "title": "Сотрудники"
    })



@login_required
def employee_add(request):
    form = EmployeeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("employee_list")
    return render(request, "employees/employee_form.html", {"form": form, "title": "Добавить сотрудника"})


@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employees, pk=pk)
    form = EmployeeForm(request.POST or None, instance=employee)

    if request.method == "POST":
        if form.is_valid():
            try:
                form.save()
                return redirect("employee_list")
            except IntegrityError:
                form.add_error(None, "Ошибка БД. Проверьте телефон, email или паспорт.")
    
    return render(request, "employees/employee_form.html", {
        "form": form,
        "title": "Редактировать сотрудника"
    })


@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employees, pk=pk)
    employee.delete()
    return redirect("employee_list")


def generate_contract_report(path):
    pdf = canvas.Canvas(path, pagesize=A4)
    font_path = os.path.join(settings.BASE_DIR, "rental", "static", "fonts", "DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont("DejaVu", font_path))

    pdf.setFont("DejaVu", 16)
    pdf.drawString(150, 800, "ОТЧЁТ ПО ДОГОВОРАМ АРЕНДЫ")

    pdf.setFont("DejaVu", 11)
    y = 760

    contracts = Contracts.objects.select_related("client", "car").all()

    for c in contracts:
        if y < 120:
            pdf.showPage()
            pdf.setFont("DejaVu", 11)
            y = 800

        lines = [
            f"Договор #{c.contract_id}",
            f"Дата создания: {c.created_at}",
            f"Период аренды: {c.issue_date} → {c.return_date}",
            f"Клиент: {c.client.full_name}",
            f"Авто: {c.car.plate} ({c.car.brand} {c.car.model})",
            f"Стоимость: {c.total_amount} руб.",
            "-" * 80,
        ]

        for line in lines:
            pdf.drawString(40, y, line)
            y -= 18

    pdf.save()


@login_required
def report_contracts(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="contracts_report.pdf"'

    temp_path = os.path.join(settings.BASE_DIR, "contracts_report.pdf")

    t = threading.Thread(target=generate_contract_report, args=(temp_path,))
    t.start()
    t.join()

    with open(temp_path, "rb") as f:
        response.write(f.read())

    os.remove(temp_path)
    return response


def generate_cars_report(path):
    pdf = canvas.Canvas(path, pagesize=A4)
    font_path = os.path.join(settings.BASE_DIR, "rental", "static", "fonts", "DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont("DejaVu", font_path))

    pdf.setFont("DejaVu", 16)
    pdf.drawString(120, 800, "ОТЧЁТ: ВОСТРЕБОВАННОСТЬ АВТОМОБИЛЕЙ")

    pdf.setFont("DejaVu", 11)
    y = 760

    cars = Cars.objects.select_related("status", "category").all()

    cars_with_stats = []

    for car in cars:
        contracts = Contracts.objects.filter(car=car).select_related("client").order_by("-created_at")
        count = contracts.count()
        last_contract = contracts.first()

        cars_with_stats.append({
            "car": car,
            "count": count,
            "last_client": last_contract.client.full_name if last_contract else "Нет",
            "last_date": last_contract.created_at if last_contract else "—",
        })

    cars_sorted = sorted(cars_with_stats, key=lambda x: x["count"], reverse=True)

    for item in cars_sorted:
        car = item["car"]
        count = item["count"]
        last_client = item["last_client"]
        last_date = item["last_date"]

        if y < 140:
            pdf.showPage()
            pdf.setFont("DejaVu", 11)
            y = 800

        lines = [
            f"Автомобиль: {car.plate} — {car.brand} {car.model}",
            f"Категория: {car.category.name}",
            f"Статус: {car.status.status}",
            f"Количество договоров: {count}",
            f"Последняя сдача: {last_date}",
            f"Последний клиент: {last_client}",
            "-" * 80,
        ]

        for line in lines:
            pdf.drawString(40, y, line)
            y -= 18

    pdf.save()


@login_required
def report_cars(request):
    path = io.BytesIO()

    thread = threading.Thread(target=generate_cars_report, args=(path,))
    thread.start()
    thread.join()

    pdf_bytes = path.getvalue()
    path.close()

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="cars_report.pdf"'
    return response


@login_required
def reports_page(request):
    return render(request, "reports.html")


@login_required
def dashboard_revenue(request):
    monthly = (
        Contracts.objects
        .values("created_at__year", "created_at__month")
        .annotate(revenue=Sum("total_amount"))
        .order_by("created_at__year", "created_at__month")
    )

    labels = [f"{row['created_at__year']}-{row['created_at__month']:02d}" for row in monthly]
    revenue = [float(row["revenue"] or 0) for row in monthly]

    context = {
        "title": "Прибыль по месяцам",
        "labels": json.dumps(labels),
        "labels_list": labels,
        "values": json.dumps(revenue),
        "dataset_label": "Прибыль (руб.)",
        "chart_type": "line",
        "fill_area": True,
    }
    return render(request, "dashboard_single.html", context)


@login_required
def dashboard_contracts(request):
    monthly = (
        Contracts.objects
        .values("created_at__year", "created_at__month")
        .annotate(count=Count("contract_id"))
        .order_by("created_at__year", "created_at__month")
    )

    labels = [f"{row['created_at__year']}-{row['created_at__month']:02d}" for row in monthly]
    count = [int(row["count"] or 0) for row in monthly]

    context = {
        "title": "Количество договоров по месяцам",
        "labels": json.dumps(labels),
        "labels_list": labels,
        "values": json.dumps(count),
        "dataset_label": "Кол-во договоров",
        "chart_type": "bar",
        "fill_area": False,
    }
    return render(request, "dashboard_single.html", context)


@login_required
def dashboard_avgcheck(request):
    monthly = (
        Contracts.objects
        .values("created_at__year", "created_at__month")
        .annotate(avg_check=Avg("total_amount"))
        .order_by("created_at__year", "created_at__month")
    )

    labels = [f"{row['created_at__year']}-{row['created_at__month']:02d}" for row in monthly]
    avg_check = [float(row["avg_check"] or 0) for row in monthly]

    context = {
        "title": "Средний чек по месяцам",
        "labels": json.dumps(labels),
        "labels_list": labels,
        "values": json.dumps(avg_check),
        "dataset_label": "Средний чек (руб.)",
        "chart_type": "line",
        "fill_area": True,
    }
    return render(request, "dashboard_single.html", context)


@login_required
def dashboard_categories(request):
    categories = (
        Contracts.objects
        .values("car__category__name")
        .annotate(revenue=Sum("total_amount"))
        .order_by("-revenue")
    )

    labels = [c["car__category__name"] or "Не указано" for c in categories]
    revenue = [float(c["revenue"] or 0) for c in categories]

    context = {
        "title": "Выручка по категориям автомобилей",
        "labels": json.dumps(labels),
        "labels_list": labels,
        "values": json.dumps(revenue),
        "dataset_label": "Выручка (руб.)",
        "chart_type": "pie",
        "fill_area": False,
    }
    return render(request, "dashboard_single.html", context)


@login_required
def dashboard_topcars(request):
    cars = (
        Contracts.objects
        .values("car__plate", "car__brand", "car__model")
        .annotate(revenue=Sum("total_amount"))
        .order_by("-revenue")[:5]
    )

    labels = [
        f"{c['car__plate']} ({c['car__brand']} {c['car__model']})"
        for c in cars
    ]
    revenue = [float(c["revenue"] or 0) for c in cars]

    context = {
        "title": "ТОП-5 автомобилей по выручке",
        "labels": json.dumps(labels),
        "labels_list": labels,
        "values": json.dumps(revenue),
        "dataset_label": "Выручка (руб.)",
        "chart_type": "bar",
        "fill_area": False,
    }
    return render(request, "dashboard_single.html", context)



@login_required
def dashboard_home(request):
    today = now().date()

    total_clients = Clients.objects.count()
    total_cars = Cars.objects.count()

    active_contracts = Contracts.objects.filter(return_date__gte=today).count()

    total_revenue = (
        Contracts.objects
        .filter(return_date__lt=today)
        .aggregate(total=Sum("total_amount"))
        .get("total") or 0
    )

    return render(request, "dashboard_home.html", {
        "total_clients": total_clients,
        "total_cars": total_cars,
        "active_contracts": active_contracts,
        "total_revenue": total_revenue,
    })





@login_required
def dashboard_revenue_json(request):
    today = now().date()

    monthly = (
        Contracts.objects
        .filter(return_date__lt=today)
        .values("return_date__year", "return_date__month")
        .annotate(revenue=Sum("total_amount"))
        .order_by("return_date__year", "return_date__month")
    )

    labels = [
        f"{row['return_date__year']}-{row['return_date__month']:02d}"
        for row in monthly
    ]
    values = [float(row["revenue"] or 0) for row in monthly]

    return JsonResponse({"labels": labels, "values": values})

@login_required
def get_car_price(request, car_id):
    car = Cars.objects.get(pk=car_id)
    return JsonResponse({"daily_price": float(car.daily_price)})
