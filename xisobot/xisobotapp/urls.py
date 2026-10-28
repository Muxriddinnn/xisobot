

from django.urls import path
from . import views

urlpatterns = [
    # Asosiy sahifa
    path("", views.dashboard, name="dashboard"),

    # Ro‘yxatdan o‘tish va tizimga kirish
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Kirim va chiqim amallari
    path("add/", views.add_transaction, name="add_transaction"),
    path("edit/<int:pk>/", views.edit_transaction, name="edit_transaction"),
    path("delete/<int:pk>/", views.delete_transaction, name="delete_transaction"),
]
