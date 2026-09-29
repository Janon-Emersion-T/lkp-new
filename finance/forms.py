from pages.forms import DashboardModelForm

from .models import Expense, Invoice, Payment


class InvoiceForm(DashboardModelForm):
    class Meta:
        model = Invoice
        fields = '__all__'


class PaymentForm(DashboardModelForm):
    class Meta:
        model = Payment
        fields = '__all__'


class ExpenseForm(DashboardModelForm):
    class Meta:
        model = Expense
        fields = '__all__'
