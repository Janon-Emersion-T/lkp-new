import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pages', '0007_remove_websitesection_page_delete_mediaasset_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='Invoice',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('invoice_number', models.CharField(max_length=40, unique=True)),
                        ('status', models.CharField(choices=[('draft', 'Draft'), ('sent', 'Sent'), ('paid', 'Paid'), ('overdue', 'Overdue'), ('cancelled', 'Cancelled')], default='draft', max_length=20)),
                        ('issue_date', models.DateField(blank=True, null=True)),
                        ('due_date', models.DateField(blank=True, null=True)),
                        ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                        ('tax', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                        ('total', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                        ('notes', models.TextField(blank=True)),
                        ('billing_period', models.DateField(blank=True, null=True)),
                        ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='pages.client')),
                        ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='pages.project')),
                        ('quotation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='pages.quotation')),
                        ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='pages.hostingsubscription')),
                    ],
                    options={
                        'db_table': 'pages_invoice',
                        'ordering': ['-created_at'],
                        'constraints': [models.UniqueConstraint(fields=('subscription', 'billing_period'), name='unique_subscription_billing_period')],
                    },
                ),
                migrations.CreateModel(
                    name='Payment',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                        ('paid_at', models.DateField(default=timezone.localdate)),
                        ('method', models.CharField(blank=True, max_length=80)),
                        ('reference', models.CharField(blank=True, max_length=160)),
                        ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='pages.client')),
                        ('invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='finance.invoice')),
                    ],
                    options={
                        'db_table': 'pages_payment',
                        'ordering': ['-paid_at'],
                    },
                ),
                migrations.CreateModel(
                    name='Expense',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('title', models.CharField(max_length=220)),
                        ('category', models.CharField(blank=True, max_length=120)),
                        ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                        ('spent_at', models.DateField(default=timezone.localdate)),
                        ('notes', models.TextField(blank=True)),
                        ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expenses', to='pages.project')),
                    ],
                    options={
                        'db_table': 'pages_expense',
                        'ordering': ['-spent_at'],
                    },
                ),
            ],
        ),
    ]
