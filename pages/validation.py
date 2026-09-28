import json
from decimal import Decimal
from django.core.exceptions import ValidationError


def validate_record(obj):
    errors = {}
    for field in obj._meta.fields:
        value = getattr(obj, field.attname)
        if isinstance(value, Decimal) and value < 0:
            errors[field.name] = 'Enter a non-negative amount.'
    for start, end in [('start_date', 'due_date'), ('start_date', 'end_date'), ('start_date', 'expiry_date'), ('issue_date', 'due_date'), ('period_start', 'period_end')]:
        if getattr(obj, start, None) and getattr(obj, end, None) and getattr(obj, start) > getattr(obj, end):
            errors[end] = 'End date must be on or after the start date.'
    for field in ['score', 'probability']:
        if (getattr(obj, field, 0) or 0) > 100:
            errors[field] = 'Enter a value from 0 to 100.'
    for field in ['schema_json', 'data_json', 'config']:
        if getattr(obj, field, ''):
            try:
                json.loads(getattr(obj, field))
            except (ValueError, TypeError):
                errors[field] = 'Enter valid JSON.'
    if obj._meta.model_name == 'lead' and obj.status == 'lost' and not obj.lost_reason:
        errors['lost_reason'] = 'Provide the reason this opportunity was lost.'
    if obj._meta.model_name == 'quotationlineitem' and obj.quantity is not None and obj.quantity <= 0:
        errors['quantity'] = 'Quantity must be greater than zero.'
    if obj._meta.model_name == 'invoice' and obj.pk:
        if obj.subtotal is not None and obj.tax is not None and obj.subtotal + obj.tax < obj.amount_paid:
            errors['subtotal'] = 'Invoice total cannot be less than payments already received.'
        if obj.status in ['draft', 'cancelled'] and obj.amount_paid:
            errors['status'] = 'An invoice with payments cannot be cancelled or changed to draft.'
    if obj._meta.model_name == 'payment':
        if obj.amount is not None and obj.amount <= 0:
            errors['amount'] = 'Payment must be greater than zero.'
        if obj.invoice_id:
            if obj.invoice.status in ['draft', 'cancelled']:
                errors['invoice'] = 'Payments require an issued invoice.'
            if obj.client_id != obj.invoice.client_id:
                errors['client'] = 'Select the client on the invoice.'
            paid = sum(obj.invoice.payments.exclude(pk=obj.pk).values_list('amount', flat=True), Decimal('0'))
            if obj.amount is not None and paid + obj.amount > obj.invoice.total:
                errors['amount'] = 'Payment exceeds the outstanding invoice balance.'
    if obj._meta.model_name == 'projecttask' and obj.milestone_id and obj.milestone.project_id != obj.project_id:
        errors['milestone'] = 'The milestone must belong to this project.'
    if obj._meta.model_name == 'supportticket' and obj.project_id and obj.project.client_id != obj.client_id:
        errors['project'] = 'Project must belong to the selected client.'
    if obj._meta.model_name == 'redirectrule':
        if obj.status_code not in [301, 302, 307, 308]:
            errors['status_code'] = 'Use 301, 302, 307, or 308.'
        if not obj.from_path.startswith('/') or obj.from_path.startswith('//'):
            errors['from_path'] = 'Enter a local path beginning with /.'
        if not obj.to_path.startswith('/') or obj.to_path.startswith('//'):
            errors['to_path'] = 'Enter a local destination beginning with /.'
        if obj.from_path == obj.to_path:
            errors['to_path'] = 'Destination must differ from the source.'
    if errors:
        raise ValidationError(errors)
