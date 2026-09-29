import csv
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from uuid import uuid4
from xml.sax.saxutils import escape

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import Http404, HttpResponse, FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .access import allowed, audit, require_permission, staff_required
from . import models as m


def context(request, resource, title):
    from .views import nav_for
    return {'nav_items': nav_for(request), 'active_resource': resource, 'title': title}


def csv_response(name, headers, rows):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{name.lower().replace(" ", "-")}.csv"'
    writer = csv.writer(response)
    def cell(value):
        text = str(value) if value is not None else ''
        return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text
    writer.writerow(headers)
    writer.writerows([[cell(value) for value in row] for row in rows])
    return response


def action_options(user, resource, obj):
    result = []
    if not allowed(user, type(obj), 'change'):
        return result
    if resource == 'quotations':
        if obj.status == 'draft':
            result.append(('issue', 'Mark as sent'))
        if obj.status in ['draft', 'sent']:
            result.extend([('approve', 'Approve'), ('reject', 'Reject')])
        if allowed(user, m.Quotation, 'add'):
            result.append(('revise', 'Create revision'))
        if obj.status == 'approved' and obj.client_id:
            if allowed(user, m.Project, 'add'):
                result.append(('project', 'Create project'))
            if allowed(user, m.Invoice, 'add'):
                result.append(('invoice', 'Create invoice'))
    if resource == 'invoices' and obj.status == 'draft':
        result.append(('issue', 'Issue invoice'))
    if resource == 'follow-ups' and obj.status != 'done':
        result.append(('complete', 'Complete follow-up'))
    if resource == 'leads' and allowed(user, m.Client, 'add'):
        result.append(('client', 'Convert to client'))
    if resource == 'hosting-subscriptions' and obj.client_id and obj.expiry_date and obj.status != 'cancelled' and allowed(user, m.Invoice, 'add'):
        result.append(('renewal-invoice', 'Create renewal invoice'))
    return result


@staff_required
def detail(request, resource, pk):
    from .views import _get_resource, _display_value, CRUD_RESOURCES
    config = _get_resource(resource)
    require_permission(request.user, config['model'])
    obj = get_object_or_404(config['model'], pk=pk)
    fields = []
    for field in obj._meta.fields:
        if field.name in ['password', 'id']:
            continue
        if field.is_relation and field.related_model and not allowed(request.user, field.related_model):
            continue
        fields.append((field.verbose_name.title(), _display_value(obj, field.name)))
    related = []
    relation_map = {
        'clients': [('projects', 'client'), ('quotations', 'client'), ('invoices', 'client'), ('payments', 'client'), ('client-communications', 'client'), ('client-files', 'client'), ('client-credentials', 'client'), ('hosting-subscriptions', 'client'), ('support-tickets', 'client')],
        'projects': [('project-milestones', 'project'), ('project-tasks', 'project'), ('project-files', 'project'), ('invoices', 'project'), ('expenses', 'project')],
        'quotations': [('quotation-line-items', 'quotation'), ('projects', 'quotation'), ('invoices', 'quotation')],
        'leads': [('follow-ups', 'lead'), ('quotations', 'lead')],
        'companies': [('contacts', 'company'), ('leads', 'company')],
        'invoices': [('payments', 'invoice')],
        'employees': [('project-tasks', 'employee')],
        'hosting-subscriptions': [('invoices', 'subscription')],
        'newsletters': [('newsletter-deliveries', 'newsletter')],
        'case-studies': [('case-study-gallery', 'case_study'), ('case-study-metrics', 'case_study')],
    }
    for key, fk in relation_map.get(resource, []):
        model = CRUD_RESOURCES[key]['model']
        if allowed(request.user, model):
            records = model.objects.filter(**{fk: obj}).order_by('-pk')
            related.append({'title': CRUD_RESOURCES[key]['title'], 'resource': key, 'fk': fk, 'items': records[:15], 'count': records.count(), 'can_add': allowed(request.user, model, 'add')})
    duplicates = []
    if resource == 'leads':
        match = Q(email__iexact=obj.email)
        if obj.phone:
            match |= Q(phone=obj.phone)
        duplicates = m.Lead.objects.filter(match).exclude(pk=obj.pk)
    financials = []
    if resource == 'invoices':
        financials = [('Invoice total', obj.total), ('Paid', obj.amount_paid), ('Balance', obj.balance)]
    elif resource == 'clients' and allowed(request.user, m.Invoice):
        invoices = obj.invoices.exclude(status__in=['draft', 'cancelled']).prefetch_related('payments')
        financials = [('Invoiced', sum(i.total for i in invoices)), ('Paid', sum(i.amount_paid for i in invoices)), ('Outstanding', sum(i.balance for i in invoices))]
    elif resource == 'projects' and allowed(request.user, m.Expense):
        cost = obj.expenses.aggregate(total=Sum('amount'))['total'] or 0
        financials = [('Budget', obj.budget), ('Expenses', cost), ('Estimated margin', obj.budget - cost)]
    data = context(request, resource, str(obj))
    data.update(config=config, resource=resource, object=obj, fields=fields, related=related, duplicates=duplicates, financials=financials,
                actions=action_options(request.user, resource, obj), can_change=allowed(request.user, type(obj), 'change') and not config.get('readonly'),
                can_convert=resource == 'enquiries' and allowed(request.user, m.Lead, 'add') and allowed(request.user, m.Enquiry, 'change'),
                can_pdf=resource in ['quotations', 'invoices', 'payments'] or resource == 'clients' and allowed(request.user, m.Invoice),
                can_add_item=resource == 'quotations' and allowed(request.user, m.QuotationLineItem, 'add'),
                packages=m.ServicePackage.objects.filter(is_active=True) if resource == 'quotations' else [])
    if resource in ['insights', 'portfolios', 'case-studies', 'cms-pages', 'service-packages', 'industries', 'markets']:
        kind = {'insights': 'insights', 'portfolios': 'portfolio', 'case-studies': 'case-studies', 'cms-pages': 'pages', 'service-packages': 'services', 'industries': 'industries', 'markets': 'markets'}[resource]
        if getattr(obj, 'status', 'published') == 'published' and getattr(obj, 'is_active', True):
            data['public_url'] = f'/{kind}/{obj.slug}/'
    return render(request, 'dashboard/detail.html', data)


@staff_required
@require_POST
def action(request, resource, pk, operation):
    from .views import _get_resource
    model = _get_resource(resource)['model']
    require_permission(request.user, model, 'change')
    target_resource, target_pk = resource, pk
    try:
        with transaction.atomic():
            obj = get_object_or_404(model.objects.select_for_update(), pk=pk)
            if operation not in dict(action_options(request.user, resource, obj)) and not (resource == 'quotations' and operation == 'package'):
                raise ValidationError('This action is not available in the current state.')
            if resource == 'quotations':
                if operation in ['approve', 'issue', 'project', 'invoice']:
                    if not obj.line_items.exists() or obj.total <= 0:
                        raise ValidationError('Add priced line items before continuing.')
                    if obj.valid_until and obj.valid_until < timezone.localdate():
                        raise ValidationError('This quotation has expired. Create a revision first.')
                if operation == 'package':
                    require_permission(request.user, m.QuotationLineItem, 'add')
                    if obj.status != 'draft':
                        raise ValidationError('Packages can only be added to draft quotations.')
                    package = get_object_or_404(m.ServicePackage, pk=request.POST.get('package'), is_active=True)
                    m.QuotationLineItem.objects.create(quotation=obj, package=package, description=package.title, quantity=Decimal('1'), unit_price=package.price)
                elif operation in ['approve', 'reject', 'issue']:
                    obj.status = {'approve': 'approved', 'reject': 'rejected', 'issue': 'sent'}[operation]
                    obj.save()
                elif operation == 'revise':
                    items = list(obj.line_items.all())
                    original = obj.pk
                    obj.pk = None
                    obj.quote_number = f'Q-{timezone.localdate():%Y%m%d}-{uuid4().hex[:8].upper()}'
                    obj.revised_from_id = original
                    obj.revision += 1
                    obj.status = 'draft'
                    obj.valid_until = timezone.localdate() + timedelta(days=30)
                    obj.save()
                    for item in items:
                        item.pk, item.quotation = None, obj
                        item.save()
                    target_pk = obj.pk
                elif operation == 'project':
                    project = obj.projects.first()
                    if not project:
                        project = m.Project.objects.create(quotation=obj, client=obj.client, name=obj.title, budget=obj.total, requirements=obj.notes)
                    target_resource, target_pk = 'projects', project.pk
                elif operation == 'invoice':
                    invoice = obj.invoices.first()
                    if not invoice:
                        invoice = m.Invoice.objects.create(quotation=obj, client=obj.client, project=obj.projects.first(), invoice_number=f'INV-{timezone.localdate():%Y%m%d}-{uuid4().hex[:8].upper()}', subtotal=obj.subtotal - obj.discount, tax=obj.tax, total=obj.total, issue_date=timezone.localdate(), due_date=timezone.localdate() + timedelta(days=30), notes=obj.notes)
                    target_resource, target_pk = 'invoices', invoice.pk
            elif resource == 'leads':
                client = m.Client.objects.filter(company=obj.company).first() if obj.company_id else None
                client = client or m.Client.objects.filter(email__iexact=obj.email).first()
                if not client:
                    client = m.Client.objects.create(name=obj.company.name if obj.company else obj.name, company=obj.company, email=obj.email, phone=obj.phone)
                obj.status = 'won'
                obj.save()
                target_resource, target_pk = 'clients', client.pk
            elif resource == 'invoices':
                if obj.total <= 0 or not obj.client_id:
                    raise ValidationError('An invoice needs a client and a positive total.')
                obj.status = 'sent'
                obj.issue_date = obj.issue_date or timezone.localdate()
                obj.save()
            elif resource == 'follow-ups':
                obj.status = 'done'
                obj.save()
            elif resource == 'hosting-subscriptions':
                if obj.renewal_amount <= 0:
                    raise ValidationError('Enter a positive renewal amount.')
                invoice, _ = m.Invoice.objects.get_or_create(subscription=obj, billing_period=obj.expiry_date, defaults={'client': obj.client, 'invoice_number': f'REN-{uuid4().hex[:10].upper()}', 'subtotal': obj.renewal_amount, 'total': obj.renewal_amount, 'issue_date': timezone.localdate(), 'due_date': obj.expiry_date, 'notes': f'Renewal: {obj.service_type} {obj.domain}'})
                target_resource, target_pk = 'invoices', invoice.pk
            audit(request.user, operation.replace('-', ' ').title(), obj)
        messages.success(request, 'Action completed.')
    except ValidationError as error:
        messages.error(request, '; '.join(error.messages))
    return redirect('dashboard_detail', resource=target_resource, pk=target_pk)


@staff_required
def board(request, resource):
    if resource not in ['leads', 'project-tasks']:
        raise Http404
    model = m.Lead if resource == 'leads' else m.ProjectTask
    require_permission(request.user, model)
    objects = model.objects.all().select_related()
    project = request.GET.get('project', '')
    if resource == 'project-tasks' and project.isdigit():
        objects = objects.filter(project_id=project)
    columns = [{'value': value, 'label': label, 'items': list(objects.filter(status=value))} for value, label in model.Status.choices]
    data = context(request, resource, 'Sales Pipeline' if resource == 'leads' else 'Project Board')
    data.update(resource=resource, columns=columns, statuses=model.Status.choices, can_change=allowed(request.user, model, 'change'), project=project)
    return render(request, 'dashboard/board.html', data)


@staff_required
@require_POST
def move_card(request, resource, pk):
    if resource not in ['leads', 'project-tasks']:
        raise Http404
    model = m.Lead if resource == 'leads' else m.ProjectTask
    require_permission(request.user, model, 'change')
    with transaction.atomic():
        obj = get_object_or_404(model.objects.select_for_update(), pk=pk)
        status = request.POST.get('status')
        if status not in model.Status.values:
            return HttpResponse('Invalid status', status=400)
        obj.status = status
        if resource == 'leads' and status == 'lost':
            obj.lost_reason = request.POST.get('lost_reason', '').strip() or obj.lost_reason
        try:
            obj.full_clean()
            obj.save()
            audit(request.user, f'Moved to {obj.get_status_display()}', obj)
            messages.success(request, 'Status updated.')
        except ValidationError as error:
            messages.error(request, '; '.join(error.messages))
    url = reverse('dashboard_board', kwargs={'resource': resource})
    if resource == 'project-tasks' and request.POST.get('project', '').isdigit():
        url += f'?project={request.POST["project"]}'
    return redirect(url)


def report_data(start, end):
    payments = m.Payment.objects.filter(paid_at__range=(start, end))
    expenses = m.Expense.objects.filter(spent_at__range=(start, end))
    leads = m.Lead.objects.filter(created_at__date__range=(start, end))
    enquiries = m.Enquiry.objects.filter(created_at__date__range=(start, end))
    revenue = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    costs = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    won = leads.filter(status='won').count()
    count = leads.count()
    outstanding = sum(i.balance for i in m.Invoice.objects.exclude(status__in=['cancelled', 'draft']).prefetch_related('payments'))
    metrics = [('Collected revenue', revenue), ('Expenses', costs), ('Net cash flow', revenue - costs), ('Outstanding now', outstanding), ('New leads', count), ('Won leads', won), ('Lead conversion %', round(won / count * 100, 1) if count else 0), ('New clients', m.Client.objects.filter(created_at__date__range=(start, end)).count()), ('Website enquiries', enquiries.count()), ('Enquiries converted', enquiries.filter(converted_lead__isnull=False).count())]
    sections = []
    sections.append({'title': 'Lead sources', 'headers': ['Source', 'Leads', 'Value'], 'rows': [(row['lead_source__name'] or row['source'], row['count'], row['value']) for row in leads.values('lead_source__name', 'source').annotate(count=Count('pk'), value=Sum('estimated_value')).order_by('-count')]})
    sections.append({'title': 'Sales funnel', 'headers': ['Stage', 'Leads', 'Value'], 'rows': [(row['status'], row['count'], row['value']) for row in leads.values('status').annotate(count=Count('pk'), value=Sum('estimated_value')).order_by('status')]})
    sections.append({'title': 'Project profitability', 'headers': ['Project', 'Budget', 'Expenses', 'Estimated margin'], 'rows': [(p.name, p.budget, sum(e.amount for e in p.expenses.all()), p.budget - sum(e.amount for e in p.expenses.all())) for p in m.Project.objects.prefetch_related('expenses')]})
    from django.db.models.functions import TruncMonth
    sections.append({'title': 'Monthly receipts', 'headers': ['Month', 'Collected'], 'rows': [(row['month'], row['amount']) for row in payments.annotate(month=TruncMonth('paid_at')).values('month').annotate(amount=Sum('amount')).order_by('month')]})
    sections.append({'title': 'Service performance', 'headers': ['Service', 'Leads', 'Value'], 'rows': [(row['service'] or 'Unspecified', row['count'], row['value']) for row in leads.values('service').annotate(count=Count('pk'), value=Sum('estimated_value')).order_by('-count')]})
    sections.append({'title': 'Campaign attribution', 'headers': ['Campaign', 'Source', 'Enquiries', 'Converted'], 'rows': [(row['utm_campaign'] or 'Unattributed', row['utm_source'] or 'Direct', row['count'], row['converted']) for row in enquiries.values('utm_campaign', 'utm_source').annotate(count=Count('pk'), converted=Count('pk', filter=Q(converted_lead__isnull=False))).order_by('-count')]})
    return metrics, sections


@staff_required
def reports(request):
    for model in [m.ReportSnapshot, m.Payment, m.Expense, m.Lead, m.Enquiry, m.Client, m.Invoice, m.Project]:
        require_permission(request.user, model)
    today = timezone.localdate()
    try:
        start = date.fromisoformat(request.GET.get('start', today.replace(day=1).isoformat()))
        end = date.fromisoformat(request.GET.get('end', today.isoformat()))
        if end < start:
            raise ValueError
    except ValueError:
        messages.error(request, 'Enter a valid date range.')
        start, end = today.replace(day=1), today
    metrics, sections = report_data(start, end)
    if request.GET.get('export') == 'csv':
        rows = list(metrics)
        for section in sections:
            rows.extend([[], [section['title']], section['headers'], *section['rows']])
        return csv_response('business-report', ['Metric', 'Value'], rows)
    if request.method == 'POST':
        require_permission(request.user, m.ReportSnapshot, 'add')
        import json
        snapshot = m.ReportSnapshot.objects.create(title=f'Business report: {start} to {end}', report_type='business', period_start=start, period_end=end, data_json=json.dumps({'metrics': metrics, 'sections': sections}, default=str))
        audit(request.user, 'Generated report', snapshot)
        return redirect('dashboard_detail', resource='report-snapshots', pk=snapshot.pk)
    data = context(request, 'reports', 'Business Reports')
    data.update(metrics=metrics, sections=sections, start=start, end=end, can_snapshot=allowed(request.user, m.ReportSnapshot, 'add'))
    return render(request, 'dashboard/reports.html', data)


@staff_required
def document(request, resource, pk):
    from .views import _get_resource
    if resource not in ['quotations', 'invoices', 'payments', 'clients']:
        raise Http404
    model = _get_resource(resource)['model']
    require_permission(request.user, model)
    obj = get_object_or_404(model, pk=pk)
    if resource == 'clients':
        require_permission(request.user, m.Invoice)
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    styles = getSampleStyleSheet()
    buffer = BytesIO()
    def para(value, style='BodyText'):
        return Paragraph(escape(str(value)), styles[style])
    heading = {'quotations': 'Quotation', 'invoices': 'Invoice', 'payments': 'Receipt', 'clients': 'Account Statement'}[resource]
    story = [para('LK Professionals', 'Title'), para(f'{heading}: {obj}', 'Heading1'), para(f'Generated {timezone.localdate()}'), Spacer(1, 16)]
    client = obj if resource == 'clients' else getattr(obj, 'client', None)
    if client:
        story.extend([para(client.name, 'Heading2'), para(client.email), para(client.billing_address), Spacer(1, 12)])
    if resource == 'quotations':
        rows = [['Description', 'Quantity', 'Unit price', 'Total']] + [[item.description, item.quantity, item.unit_price, item.total] for item in obj.line_items.all()]
        rows += [['Subtotal', '', '', obj.subtotal], ['Discount', '', '', obj.discount], ['Tax', '', '', obj.tax], ['Total', '', '', obj.total]]
        story.append(para(f'Revision {obj.revision} | Valid until: {obj.valid_until or "Not set"} | {obj.get_status_display()}'))
    elif resource == 'invoices':
        rows = [['Description', 'Amount'], ['Subtotal', obj.subtotal], ['Tax', obj.tax], ['Total', obj.total], ['Paid', obj.amount_paid], ['Balance', obj.balance]]
        story.append(para(f'Issued: {obj.issue_date or "Draft"} | Due: {obj.due_date or "Not set"}'))
    elif resource == 'payments':
        rows = [['Receipt detail', 'Value'], ['Invoice', obj.invoice or '-'], ['Date', obj.paid_at], ['Method', obj.method], ['Reference', obj.reference], ['Amount', obj.amount]]
    else:
        rows = [['Invoice', 'Due date', 'Total', 'Paid', 'Balance']] + [[i.invoice_number, i.due_date or '-', i.total, i.amount_paid, i.balance] for i in obj.invoices.exclude(status__in=['draft', 'cancelled']).prefetch_related('payments')]
    table = Table([[para(cell) for cell in row] for row in rows], repeatRows=1, hAlign='LEFT', colWidths=[480 / len(rows[0])] * len(rows[0]))
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eef2')), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BOTTOMPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 8), ('LINEBELOW', (0, 0), (-1, -1), .4, colors.HexColor('#d8dee3'))]))
    story.extend([Spacer(1, 12), table, Spacer(1, 16), para(getattr(obj, 'notes', ''))])
    SimpleDocTemplate(buffer, title=f'{heading} {obj}', author='LK Professionals').build(story)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'{resource}-{obj.pk}.pdf', content_type='application/pdf')


@staff_required
def download_file(request, path):
    from django.core.files.storage import default_storage
    file_url = f'/dashboard/files/{path}'
    permitted = any(allowed(request.user, model) and model.objects.filter(file_url=file_url).exists() for model in [m.MediaAsset, m.ClientFile, m.ProjectFile, m.BackupRecord])
    permitted = permitted or (allowed(request.user, m.CareerApplication) and m.CareerApplication.objects.filter(resume_url=file_url).exists())
    if not permitted or not path.startswith('dashboard/') or '..' in path.split('/') or not default_storage.exists(path):
        raise Http404
    return FileResponse(default_storage.open(path, 'rb'), as_attachment=True)
