from datetime import timedelta
import os
import threading

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .forms import CarForm, ClientForm, ContractForm, EmployeeForm
from .models import Cars, Clients, Contracts, Employees
from django.db.models.functions import TruncMonth
from django.db.models import Count, Sum
import json


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _is_free_status_q():
    return Q(status__status__iexact="свободен") | Q(status__status__iexact="доступен")


def login_view(request):
    if request.method == "POST":
        email = _normalize_email(request.POST.get("email", ""))
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=email, password=password)
        if user is None:
            return render(request, "login.html", {"error": "Неверный email или пароль"})
        if not user.is_active:
            return render(request, "login.html", {"error": "Пользователь отключён"})

        login(request, user)
        return redirect(request.GET.get("next") or "/")

    return render(request, "login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard_home(request):
    today = now().date()
    week_ago = today - timedelta(days=7)

    free_cars = Cars.objects.filter(_is_free_status_q()).count()
    busy_cars = Cars.objects.exclude(_is_free_status_q()).count()

    return render(request, "dashboard_home.html", {
        "total_clients": Clients.objects.count(),
        "total_cars": Cars.objects.count(),
        "active_contracts": Contracts.objects.filter(return_date__gte=today).count(),
        "free_cars": free_cars,
        "busy_cars": busy_cars,
        "contracts_today": Contracts.objects.filter(issue_date=today).count(),
        "contracts_week": Contracts.objects.filter(issue_date__gte=week_ago).count(),
        "last_contracts": Contracts.objects.select_related("client", "car").order_by("-issue_date")[:5],
    })


@login_required
def reports_page(request):
    return render(request, "reports.html")


def _register_font(pdf):
    font_path = os.path.join(settings.BASE_DIR, "rental", "static", "fonts", "DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont("DejaVu", font_path))
    pdf.setFont("DejaVu", 11)


def _contract_status_text(contract: Contracts) -> str:
    today = now().date()
    db_status = (getattr(contract.cstatus, "status", "") or "").strip().lower()

    if any(x in db_status for x in ["закры", "заверш", "окончен"]):
        return "ДОГОВОР ЗАКРЫТ"
    if contract.return_date and contract.return_date < today:
        return "ДОГОВОР ЗАВЕРШЁН"
    return "ДОГОВОР АКТИВЕН"


def generate_contract_report(path: str):
    pdf = canvas.Canvas(path, pagesize=A4)
    _register_font(pdf)

    width, height = A4
    y = height - 40

    pdf.drawCentredString(width / 2, y, "ОТЧЁТ ПО ДОГОВОРАМ АРЕНДЫ")
    y -= 25
    pdf.setFont("DejaVu", 9)
    pdf.drawCentredString(width / 2, y, f"Сформировано: {now().strftime('%d.%m.%Y %H:%M')}")
    pdf.setFont("DejaVu", 11)
    y -= 25

    contracts = (
        Contracts.objects
        .select_related("client", "car", "issue_branch", "return_branch", "cstatus")
        .order_by("-issue_date")
    )

    if not contracts.exists():
        pdf.drawString(40, y, "Договоры отсутствуют")
        pdf.save()
        return

    for c in contracts:
        if y < 190:
            pdf.showPage()
            _register_font(pdf)
            y = height - 40

        status_text = _contract_status_text(c)

        pdf.roundRect(35, y - 160, width - 70, 160, 10)

        pdf.setFont("DejaVu", 10)
        pdf.drawString(45, y - 18, f"ДОГОВОР № {c.contract_id}")
        pdf.drawRightString(width - 45, y - 18, status_text)
        pdf.line(45, y - 26, width - 45, y - 26)

        pdf.setFont("DejaVu", 11)
        ty = y - 45

        pdf.drawString(45, ty, f"Клиент: {c.client.full_name}")
        ty -= 16

        pdf.drawString(
            45, ty,
            f"Авто: {c.car.brand} {c.car.model}   |   Гос. номер: {c.car.plate}"
        )
        ty -= 16

        pdf.drawString(45, ty, f"VIN: {c.car.vin}")
        ty -= 16

        pdf.drawString(
            45, ty,
            f"Период: {c.issue_date.strftime('%d.%m.%Y')} — {c.return_date.strftime('%d.%m.%Y')}"
        )
        ty -= 16

        pdf.drawString(45, ty, f"Филиал выдачи: {c.issue_branch.name}")
        ty -= 14
        pdf.drawString(45, ty, f"Филиал возврата: {c.return_branch.name}")
        ty -= 16

        pdf.drawString(
            45, ty,
            f"Оплата: {c.payment}   |   Статус БД: {c.cstatus.status}"
        )
        ty -= 16

        pdf.drawString(
            45, ty,
            f"Цена/сутки: {c.daily_price} ₽   |   Итог: {c.total_amount} ₽"
        )

        y -= 180

    pdf.save()



@login_required
def report_contracts(request):
    tmp_dir = os.path.join(settings.BASE_DIR, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, "report_contracts.pdf")

    t = threading.Thread(target=generate_contract_report, args=(path,))
    t.start()
    t.join()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="report_contracts.pdf"'
    with open(path, "rb") as f:
        response.write(f.read())
    os.remove(path)
    return response


def generate_cars_report(path: str):
    pdf = canvas.Canvas(path, pagesize=A4)
    _register_font(pdf)

    width, height = A4
    y = height - 40

    pdf.drawCentredString(width / 2, y, "ОТЧЁТ ПО АВТОМОБИЛЯМ")
    y -= 25
    pdf.setFont("DejaVu", 9)
    pdf.drawCentredString(width / 2, y, f"Сформировано: {now().strftime('%d.%m.%Y %H:%M')}")
    pdf.setFont("DejaVu", 11)
    y -= 25

    cars = Cars.objects.select_related("category", "status", "branch").order_by("brand", "model", "plate")

    if not cars.exists():
        pdf.drawString(40, y, "Автомобили отсутствуют")
        pdf.save()
        return

    for car in cars:
        if y < 165:
            pdf.showPage()
            _register_font(pdf)
            y = height - 40

        free_label = "СВОБОДЕН/ДОСТУПЕН" if (_normalize_email(car.status.status).lower() in ["свободен", "доступен"]) else car.status.status

        pdf.roundRect(35, y - 135, width - 70, 135, 10)
        pdf.setFont("DejaVu", 10)
        pdf.drawString(45, y - 18, f"{car.brand} {car.model}")
        pdf.drawRightString(width - 45, y - 18, f"Статус: {free_label}")
        pdf.line(45, y - 26, width - 45, y - 26)

        pdf.setFont("DejaVu", 11)
        ty = y - 45
        pdf.drawString(45, ty, f"Гос. номер: {car.plate}   |   VIN: {car.vin}")
        ty -= 16
        pdf.drawString(45, ty, f"Категория: {car.category.name}   |   Филиал: {car.branch.name}")
        ty -= 16
        pdf.drawString(45, ty, f"Год: {car.year_made}   |   Пробег: {car.mileage} км")
        ty -= 16
        pdf.drawString(45, ty, f"Цена за сутки: {car.daily_price} ₽")

        y -= 155

    pdf.save()


@login_required
def report_cars(request):
    tmp_dir = os.path.join(settings.BASE_DIR, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, "report_cars.pdf")

    t = threading.Thread(target=generate_cars_report, args=(path,))
    t.start()
    t.join()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="report_cars.pdf"'
    with open(path, "rb") as f:
        response.write(f.read())
    os.remove(path)
    return response


@login_required
def car_list(request):
    search = (request.GET.get("search", "") or "").strip()
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
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("car_list")
    return render(request, "cars/car_form.html", {"form": form, "title": "Добавить авто"})


@login_required
def car_edit(request, pk):
    car = get_object_or_404(Cars, pk=pk)
    form = CarForm(request.POST or None, instance=car)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("car_list")
    return render(request, "cars/car_form.html", {"form": form, "title": "Редактировать авто"})


@login_required
def car_delete(request, pk):
    get_object_or_404(Cars, pk=pk).delete()
    return redirect("car_list")


@login_required
def client_list(request):
    search = (request.GET.get("search", "") or "").strip()
    sort = (request.GET.get("sort", "") or "").strip()

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
    else:
        clients = clients.order_by("full_name")

    return render(request, "clients/client_list.html", {"clients": clients, "search": search, "sort": sort})


@login_required
def client_add(request):
    form = ClientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("client_list")
    return render(request, "clients/client_form.html", {"form": form, "title": "Добавить клиента"})


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Clients, pk=pk)
    form = ClientForm(request.POST or None, instance=client)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("client_list")
    return render(request, "clients/client_form.html", {"form": form, "title": "Редактировать клиента"})


@login_required
def client_delete(request, pk):
    get_object_or_404(Clients, pk=pk).delete()
    return redirect("client_list")


@login_required
def contract_list(request):
    search = (request.GET.get("search", "") or "").strip()
    sort = (request.GET.get("sort", "") or "").strip()

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
    else:
        contracts = contracts.order_by("-issue_date")

    return render(request, "contracts/contract_list.html", {"contracts": contracts, "search": search, "sort": sort})


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
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("contract_list")
    return render(request, "contracts/contract_form.html", {"form": form, "title": "Редактировать договор"})


@login_required
def contract_delete(request, pk):
    get_object_or_404(Contracts, pk=pk).delete()
    return redirect("contract_list")


@login_required
def employee_list(request):
    search = (request.GET.get("search", "") or "").strip()
    sort = (request.GET.get("sort", "") or "").strip()

    employees = Employees.objects.select_related("role", "branch")

    if search:
        employees = employees.filter(
            Q(full_name__icontains=search) |
            Q(passport__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )

    if sort == "name_asc":
        employees = employees.order_by("full_name")
    elif sort == "name_desc":
        employees = employees.order_by("-full_name")
    else:
        employees = employees.order_by("full_name")

    return render(request, "employees/employee_list.html", {"employees": employees, "search": search, "sort": sort})


@login_required
def employee_add(request):
    if not request.user.is_staff:
        return HttpResponse(status=403)

    form = EmployeeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        employee = form.save()
        email = _normalize_email(employee.email)
        password = form.cleaned_data.get("password") or ""

        if not password:
            form.add_error("password", "Пароль обязателен для создания пользователя")
            return render(request, "employees/employee_form.html", {"form": form, "title": "Добавить сотрудника"})

        role_name = (employee.role.name or "").strip().lower()
        is_staff = ("админ" in role_name) or ("admin" in role_name)

        user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
        user.email = email
        user.is_active = True
        user.is_staff = is_staff
        user.set_password(password)
        user.save()

        return redirect("employee_list")

    return render(request, "employees/employee_form.html", {"form": form, "title": "Добавить сотрудника"})


@login_required
def employee_edit(request, pk):
    if not request.user.is_staff:
        return HttpResponse(status=403)

    employee = get_object_or_404(Employees, pk=pk)
    old_email = _normalize_email(employee.email)

    form = EmployeeForm(request.POST or None, instance=employee)
    if request.method == "POST" and form.is_valid():
        employee = form.save()
        new_email = _normalize_email(employee.email)
        password = (form.cleaned_data.get("password") or "").strip()

        role_name = (employee.role.name or "").strip().lower()
        is_staff = ("админ" in role_name) or ("admin" in role_name)

        if old_email != new_email:
            User.objects.filter(username=old_email).delete()

        user, _ = User.objects.get_or_create(username=new_email, defaults={"email": new_email})
        user.email = new_email
        user.is_active = True
        user.is_staff = is_staff
        if password:
            user.set_password(password)
        user.save()

        return redirect("employee_list")

    return render(request, "employees/employee_form.html", {"form": form, "title": "Редактировать сотрудника"})


@login_required
def employee_delete(request, pk):
    if not request.user.is_staff:
        return HttpResponse(status=403)

    employee = get_object_or_404(Employees, pk=pk)
    User.objects.filter(username__iexact=_normalize_email(employee.email)).delete()
    employee.delete()
    return redirect("employee_list")


@login_required
def get_car_price(request, car_id):
    car = get_object_or_404(Cars, pk=car_id)
    return JsonResponse({"daily_price": float(car.daily_price)})


@login_required
def dashboard_contracts(request):
    qs = (
        Contracts.objects
        .annotate(month=TruncMonth("issue_date"))
        .values("month")
        .annotate(cnt=Count("contract_id"))
        .order_by("month")
    )

    labels = [q["month"].strftime("%m.%Y") for q in qs]
    values = [q["cnt"] for q in qs]

    return render(request, "dashboard_single.html", {
        "title": "Количество договоров по месяцам",
        "chart_type": "line",
        "labels": json.dumps(labels),
        "values": json.dumps(values),
        "dataset_label": "Договоры",
        "fill_area": True,
    })

@login_required
def dashboard_revenue(request):
    qs = (
        Contracts.objects
        .annotate(month=TruncMonth("issue_date"))
        .values("month")
        .annotate(sum=Sum("total_amount"))
        .order_by("month")
    )

    labels = [q["month"].strftime("%m.%Y") for q in qs]
    values = [float(q["sum"]) for q in qs]

    return render(request, "dashboard_single.html", {
        "title": "Выручка по месяцам",
        "chart_type": "bar",
        "labels": json.dumps(labels),
        "values": json.dumps(values),
        "dataset_label": "Выручка ₽",
        "fill_area": False,
    })

@login_required
def dashboard_avgcheck(request):
    qs = (
        Contracts.objects
        .annotate(month=TruncMonth("issue_date"))
        .values("month")
        .annotate(avg=Sum("total_amount") / Count("contract_id"))
        .order_by("month")
    )

    labels = [q["month"].strftime("%m.%Y") for q in qs]
    values = [float(q["avg"]) for q in qs]

    return render(request, "dashboard_single.html", {
        "title": "Средний чек по месяцам",
        "chart_type": "line",
        "labels": json.dumps(labels),
        "values": json.dumps(values),
        "dataset_label": "Средний чек ₽",
        "fill_area": True,
    })


@login_required
def dashboard_categories(request):
    qs = (
        Cars.objects
        .values("category__name")
        .annotate(cnt=Count("car_id"))
    )

    labels = [q["category__name"] for q in qs]
    values = [q["cnt"] for q in qs]

    return render(request, "dashboard_single.html", {
        "title": "Распределение автомобилей по категориям",
        "chart_type": "pie",
        "labels": json.dumps(labels),
        "values": json.dumps(values),
        "labels_list": labels,
        "dataset_label": "Авто",
        "fill_area": False,
    })


@login_required
def dashboard_topcars(request):
    qs = (
        Contracts.objects
        .values("car__brand", "car__model", "car__plate")
        .annotate(sum=Sum("total_amount"))
        .order_by("-sum")[:5]
    )

    labels = [
        f'{q["car__brand"]} {q["car__model"]} ({q["car__plate"]})'
        for q in qs
    ]
    values = [float(q["sum"]) for q in qs]

    return render(request, "dashboard_single.html", {
        "title": "Автомобили с наибольшей выручкой",
        "chart_type": "bar",
        "labels": json.dumps(labels),
        "values": json.dumps(values),
        "dataset_label": "Выручка ₽",
        "fill_area": False,
    })
@login_required
def statistics_page(request):
    return render(request, "statistics.html")