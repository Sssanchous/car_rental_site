from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('', views.dashboard_home, name='dashboard_home'),
    path('dashboard/', views.dashboard_home, name='dashboard'),

    path('reports/', views.reports_page, name='reports_page'),
    path('reports/contracts/', views.report_contracts, name='report_contracts'),
    path('reports/cars/', views.report_cars, name='report_cars'),

    path('reports/dashboard/revenue/', views.dashboard_revenue, name='dashboard_revenue'),
    path('reports/dashboard/contracts/', views.dashboard_contracts, name='dashboard_contracts'),
    path('reports/dashboard/avgcheck/', views.dashboard_avgcheck, name='dashboard_avgcheck'),
    path('reports/dashboard/categories/', views.dashboard_categories, name='dashboard_categories'),
    path('reports/dashboard/topcars/', views.dashboard_topcars, name='dashboard_topcars'),

    path('reports/dashboard/revenue/json/', views.dashboard_revenue_json, name='dashboard_revenue_json'),

    path('clients/', views.client_list, name='client_list'),
    path('clients/add/', views.client_add, name='client_add'),
    path('clients/<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),

    path('cars/', views.car_list, name='car_list'),
    path('cars/add/', views.car_add, name='car_add'),
    path('cars/<int:pk>/edit/', views.car_edit, name='car_edit'),
    path('cars/<int:pk>/delete/', views.car_delete, name='car_delete'),
    path('cars/get_price/<int:car_id>/', views.get_car_price, name='get_car_price'),

    path('contracts/', views.contract_list, name='contract_list'),
    path('contracts/add/', views.contract_add, name='contract_add'),
    path('contracts/<int:pk>/edit/', views.contract_edit, name='contract_edit'),
    path('contracts/<int:pk>/delete/', views.contract_delete, name='contract_delete'),

    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_add, name='employee_add'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
]
