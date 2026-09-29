from django.contrib import admin

from .models import Expense, Invoice, Payment


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'status', 'due_date', 'total')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'client__name', 'notes')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('client', 'invoice', 'amount', 'paid_at', 'method')
    list_filter = ('paid_at', 'method')
    search_fields = ('client__name', 'invoice__invoice_number', 'reference')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'category', 'amount', 'spent_at')
    list_filter = ('category', 'spent_at')
    search_fields = ('title', 'project__name', 'notes')
