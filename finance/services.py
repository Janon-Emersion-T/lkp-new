from decimal import Decimal

from django.db.models import Sum

from .models import Expense, Invoice, Payment


def collected_revenue(start=None, end=None):
    qs = Payment.objects.all()
    if start and end:
        qs = qs.filter(paid_at__range=(start, end))
    return qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')


def expenses_total(start=None, end=None):
    qs = Expense.objects.all()
    if start and end:
        qs = qs.filter(spent_at__range=(start, end))
    return qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')


def outstanding_balance():
    return sum(invoice.balance for invoice in Invoice.objects.exclude(status__in=['cancelled', 'draft']).prefetch_related('payments'))
