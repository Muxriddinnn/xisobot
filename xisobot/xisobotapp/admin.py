

from django.contrib import admin
from .models import Transaction, ExpenseCategory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "user",
        "amount",
        "transaction_type",
        "category",
        "date",
    )

    list_filter = (
        "transaction_type",
        "category",
        "date",
    )

    search_fields = (
        "title",
        "description",
        "user__username",
    )

    date_hierarchy = "date"
    ordering = ("-date",)
