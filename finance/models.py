from decimal import Decimal

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def clean(self):
        from pages.validation import validate_record
        super().clean()
        validate_record(self)


class Invoice(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SENT = 'sent', 'Sent'
        PAID = 'paid', 'Paid'
        OVERDUE = 'overdue', 'Overdue'
        CANCELLED = 'cancelled', 'Cancelled'

    invoice_number = models.CharField(max_length=40, unique=True)
    client = models.ForeignKey('pages.Client', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    project = models.ForeignKey('pages.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    quotation = models.ForeignKey('pages.Quotation', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    subscription = models.ForeignKey('pages.HostingSubscription', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    billing_period = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'pages_invoice'
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['subscription', 'billing_period'], name='unique_subscription_billing_period')]

    def __str__(self):
        return self.invoice_number

    @property
    def amount_paid(self):
        return sum((payment.amount for payment in self.payments.all()), Decimal('0'))

    @property
    def balance(self):
        return max(self.total - self.amount_paid, Decimal('0'))

    @property
    def payment_status(self):
        if self.status == self.Status.CANCELLED:
            return self.Status.CANCELLED
        if self.total > 0 and self.balance == 0:
            return self.Status.PAID
        if self.status != self.Status.DRAFT and self.due_date and self.due_date < timezone.localdate():
            return self.Status.OVERDUE
        return self.Status.SENT if self.status == self.Status.PAID else self.status


class Payment(TimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    client = models.ForeignKey('pages.Client', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_at = models.DateField(default=timezone.localdate)
    method = models.CharField(max_length=80, blank=True)
    reference = models.CharField(max_length=160, blank=True)

    class Meta:
        db_table = 'pages_payment'
        ordering = ['-paid_at']

    def __str__(self):
        return f'{self.amount} payment'


class Expense(TimeStampedModel):
    project = models.ForeignKey('pages.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    title = models.CharField(max_length=220)
    category = models.CharField(max_length=120, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    spent_at = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'pages_expense'
        ordering = ['-spent_at']

    def __str__(self):
        return self.title
