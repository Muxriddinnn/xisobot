
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
)

from .models import Transaction, ExpenseCategory


# =========================
# REGISTRATSIYA
# =========================
def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = UserCreationForm()

    return render(
        request,
        "xisobotapp/register.html",
        {"form": form},
    )


# =========================
# LOGIN
# =========================
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(
            request,
            data=request.POST,
        )

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard")
    else:
        form = AuthenticationForm()

    return render(
        request,
        "xisobotapp/login.html",
        {"form": form},
    )


# =========================
# LOGOUT
# =========================
@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)

    return redirect("login")


# =========================
# BOSH SAHIFA
# =========================
@login_required
def dashboard(request):
    # Faqat joriy foydalanuvchining tranzaksiyalari
    transactions = (
        Transaction.objects
        .filter(user=request.user)
        .select_related("category")
        .order_by("-date", "-id")
    )

    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")
    transaction_type = request.GET.get("type", "")

    if start_date:
        transactions = transactions.filter(date__gte=start_date)

    if end_date:
        transactions = transactions.filter(date__lte=end_date)

    if transaction_type in ("income", "expense"):
        transactions = transactions.filter(
            transaction_type=transaction_type
        )

    # Jami kirim
    income = (
        transactions
        .filter(transaction_type="income")
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    # Jami chiqim
    expenses = (
        transactions
        .filter(transaction_type="expense")
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    # Oylik diagramma
    monthly_data = (
        Transaction.objects
        .filter(user=request.user)
        .annotate(month=TruncMonth("date"))
        .values("month", "transaction_type")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    months = {}

    for row in monthly_data:
        month_key = row["month"].strftime("%Y-%m")

        if month_key not in months:
            months[month_key] = {
                "income": 0,
                "expense": 0,
            }

        months[month_key][row["transaction_type"]] = float(
            row["total"]
        )

    chart_labels = list(months.keys())

    chart_income = [
        months[month]["income"]
        for month in chart_labels
    ]

    chart_expenses = [
        months[month]["expense"]
        for month in chart_labels
    ]

    # Kategoriyalar bo'yicha chiqimlar
    category_data = (
        transactions
        .filter(
            transaction_type="expense",
            category__isnull=False,
        )
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    category_labels = [
        item["category__name"]
        for item in category_data
    ]

    category_amounts = [
        float(item["total"])
        for item in category_data
    ]

    context = {
        "transactions": transactions,
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,

        "start_date": start_date,
        "end_date": end_date,
        "selected_type": transaction_type,

        "chart_labels": chart_labels,
        "chart_income": chart_income,
        "chart_expenses": chart_expenses,

        "category_labels": category_labels,
        "category_amounts": category_amounts,
    }

    return render(
        request,
        "xisobotapp/dashboard.html",
        context,
    )


# =========================
# YANGI KIRIM / CHIQIM
# =========================
@login_required
def add_transaction(request):
    categories = ExpenseCategory.objects.all()

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        amount_text = request.POST.get("amount", "")
        transaction_type = request.POST.get("transaction_type")
        category_id = request.POST.get("category")
        date = request.POST.get("date")
        description = request.POST.get("description", "").strip()

        try:
            amount = Decimal(amount_text)

            if not amount.is_finite() or amount <= 0:
                raise InvalidOperation

            if not title or not date:
                raise ValueError

            if transaction_type not in ("income", "expense"):
                raise ValueError

            category = None

            if category_id:
                category = get_object_or_404(
                    ExpenseCategory,
                    pk=category_id,
                )

            Transaction.objects.create(
                user=request.user,
                title=title,
                amount=amount,
                transaction_type=transaction_type,
                category=category,
                date=date,
                description=description,
            )

            return redirect("dashboard")

        except (InvalidOperation, ValueError, TypeError):
            return render(
                request,
                "xisobotapp/transaction_form.html",
                {
                    "categories": categories,
                    "error": (
                        "Ma'lumotlarni tekshiring. "
                        "Summa musbat son bo'lishi kerak."
                    ),
                },
            )

    return render(
        request,
        "xisobotapp/transaction_form.html",
        {"categories": categories},
    )


# =========================
# TAHRIRLASH
# =========================
@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(
        Transaction,
        pk=pk,
        user=request.user,
    )

    categories = ExpenseCategory.objects.all()

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        amount_text = request.POST.get("amount", "")
        transaction_type = request.POST.get("transaction_type")
        category_id = request.POST.get("category")
        date = request.POST.get("date")
        description = request.POST.get("description", "").strip()

        try:
            amount = Decimal(amount_text)

            if not amount.is_finite() or amount <= 0:
                raise InvalidOperation

            if not title or not date:
                raise ValueError

            if transaction_type not in ("income", "expense"):
                raise ValueError

            category = None

            if category_id:
                category = get_object_or_404(
                    ExpenseCategory,
                    pk=category_id,
                )

            transaction.title = title
            transaction.amount = amount
            transaction.transaction_type = transaction_type
            transaction.category = category
            transaction.date = date
            transaction.description = description
            transaction.save()

            return redirect("dashboard")

        except (InvalidOperation, ValueError, TypeError):
            return render(
                request,
                "xisobotapp/transaction_form.html",
                {
                    "categories": categories,
                    "transaction": transaction,
                    "error": (
                        "Ma'lumotlarni tekshiring. "
                        "Summa musbat son bo'lishi kerak."
                    ),
                },
            )

    return render(
        request,
        "xisobotapp/transaction_form.html",
        {
            "categories": categories,
            "transaction": transaction,
        },
    )


# =========================
# O'CHIRISH
# =========================
@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(
        Transaction,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        transaction.delete()

    return redirect("dashboard")
