from hr.models import CareerApplication
from datetime import timedelta
from decimal import Decimal
from io import BytesIO, StringIO
import tempfile
from unittest.mock import patch
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from django.core.management import call_command, CommandError
from django.test import TestCase, Client as TestClient, override_settings
from django.utils import timezone
from case_studies import models as case_models
from finance import models as finance_models
from . import models as m
from .forms import AccessRoleForm
from .views import CRUD_RESOURCES, _get_form_class


def uploaded_png(name):
    buffer = BytesIO()
    Image.new('RGB', (1, 1), '#33b6ff').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser('test-admin', 'admin@example.com', 'test-password-123')
        cls.staff = get_user_model().objects.create_user('test-staff', is_staff=True)
        cls.customer = m.Client.objects.create(name='Example client', email='client@example.com')

    def setUp(self):
        self.client.force_login(self.admin)

    def url(self, resource, obj=None, suffix=''):
        return f'/dashboard/{resource}/' + (f'{obj.pk}/' if obj else '') + suffix

    def quote(self):
        quote = m.Quotation.objects.create(quote_number='Q-TEST', title='Website', client=self.customer, discount=Decimal('10'), tax=Decimal('5'))
        m.QuotationLineItem.objects.create(quotation=quote, description='Design', quantity=Decimal('2'), unit_price=Decimal('100'))
        quote.refresh_from_db()
        return quote

    def invoice(self):
        return finance_models.Invoice.objects.create(invoice_number='INV-TEST', client=self.customer, subtotal=100, total=100, status='sent', due_date=timezone.localdate() - timedelta(days=1))

    def test_all_resource_pages(self):
        for resource, config in CRUD_RESOURCES.items():
            with self.subTest(resource=resource):
                self.assertEqual(self.client.get(self.url(resource)).status_code, 200)
                self.assertEqual(self.client.get(self.url(resource, suffix='new/')).status_code, 403 if config.get('readonly') else 200)
        for path in ['/dashboard/', '/dashboard/reports/', '/dashboard/leads/board/', '/dashboard/project-tasks/board/']:
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_anonymous_and_nonstaff_denied(self):
        self.client.logout()
        self.assertEqual(self.client.get('/dashboard/').status_code, 302)
        self.client.force_login(get_user_model().objects.create_user('public-person'))
        self.assertEqual(self.client.get('/dashboard/').status_code, 403)

    def test_role_permissions_enforced(self):
        role = m.AccessRole.objects.create(name='Editorial', permissions='pages.view_tag pages.add_tag')
        role.users.add(self.staff)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get('/dashboard/tags/').status_code, 200)
        self.assertEqual(self.client.get('/dashboard/invoices/?export=csv').status_code, 403)
        self.assertEqual(self.client.get('/dashboard/access-roles/').status_code, 403)
        self.assertEqual(self.client.post('/dashboard/tags/new/', {'name': 'Tag', 'is_active': True}).status_code, 302)
        tag = m.Tag.objects.get(name='Tag')
        self.assertEqual(self.client.post(self.url('tags', tag, 'delete/')).status_code, 403)
        role.is_active = False
        role.save()
        self.assertEqual(self.client.get('/dashboard/tags/').status_code, 403)

    def test_role_editor_roundtrip(self):
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(content_type__app_label='pages', codename='view_lead')
        form = AccessRoleForm({'name': 'Sales', 'permissions': [permission.pk], 'users': [self.staff.pk], 'is_active': True})
        self.assertTrue(form.is_valid(), form.errors)
        role = form.save()
        self.assertEqual(role.permissions, 'pages.view_lead')
        self.assertIn(self.staff, role.users.all())
        self.assertEqual(list(AccessRoleForm(instance=role).initial['permissions']), [permission])

    def test_tag_crud_audit_and_unique_auto_slugs(self):
        for _ in range(2):
            self.assertEqual(self.client.post('/dashboard/tags/new/', {'name': 'Digital', 'is_active': True}).status_code, 302)
        self.assertEqual(set(m.Tag.objects.values_list('slug', flat=True)), {'digital', 'digital-2'})
        tag = m.Tag.objects.first()
        self.assertEqual(self.client.post(self.url('tags', tag, 'edit/'), {'name': 'Updated', 'slug': tag.slug, 'is_active': True}).status_code, 302)
        self.assertEqual(self.client.post(self.url('tags', tag, 'delete/')).status_code, 302)
        self.assertEqual(m.AuditLog.objects.count(), 4)
        self.assertEqual(self.client.post(self.url('audit-logs', m.AuditLog.objects.first(), 'delete/')).status_code, 403)

    def test_user_password_not_exposed_or_overwritten(self):
        self.assertNotContains(self.client.get(self.url('users', self.admin, 'edit/')), self.admin.password)
        old = self.admin.password
        response = self.client.post(self.url('users', self.admin, 'edit/'), {'username': self.admin.username, 'email': self.admin.email, 'password': '', 'is_staff': True, 'is_active': True})
        self.assertEqual(response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.password, old)

    def test_self_deactivation_blocked(self):
        self.client.post(self.url('users', self.admin, 'edit/'), {'username': self.admin.username, 'is_staff': True, 'password': ''})
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_conversion_is_post_only_and_idempotent(self):
        enquiry = m.Enquiry.objects.create(name='Person', email='p@example.com', message='Website')
        url = self.url('enquiries', enquiry, 'convert/')
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(m.Lead.objects.count(), 1)
        other = m.Enquiry.objects.create(name='Person', email='P@example.com', message='Follow-up')
        self.client.post(self.url('enquiries', other, 'convert/'))
        self.assertEqual(m.Lead.objects.count(), 1)
        other.refresh_from_db()
        self.assertEqual(other.status, 'converted')

    def test_csrf_required_for_conversion(self):
        browser = TestClient(enforce_csrf_checks=True)
        browser.force_login(self.admin)
        enquiry = m.Enquiry.objects.create(name='Person', email='p@example.com', message='Website')
        self.assertEqual(browser.post(self.url('enquiries', enquiry, 'convert/')).status_code, 403)

    def test_quote_calculation_and_line_deletion(self):
        quote = self.quote()
        self.assertEqual(quote.total, Decimal('195'))
        item = quote.line_items.first()
        item.quantity = Decimal('3')
        item.save()
        quote.refresh_from_db()
        self.assertEqual(quote.total, Decimal('295'))
        item.delete()
        quote.refresh_from_db()
        self.assertEqual(quote.subtotal, Decimal('0'))

    def test_quote_conversion_and_revision(self):
        quote = self.quote()
        self.client.post(self.url('quotations', quote, 'action/approve/'))
        quote.refresh_from_db()
        self.assertEqual(quote.status, 'approved')
        for _ in range(2):
            self.client.post(self.url('quotations', quote, 'action/project/'))
            self.client.post(self.url('quotations', quote, 'action/invoice/'))
        self.assertEqual(quote.projects.count(), 1)
        self.assertEqual(quote.invoices.count(), 1)
        self.assertEqual(quote.invoices.get().total, quote.total)
        self.client.post(self.url('quotations', quote, 'action/revise/'))
        revision = quote.revisions.get()
        self.assertEqual(revision.status, 'draft')
        self.assertEqual(revision.revision, 2)
        self.assertEqual(revision.total, quote.total)
        self.assertEqual(revision.line_items.count(), 1)

    def test_expired_quote_cannot_approve(self):
        quote = self.quote()
        quote.valid_until = timezone.localdate() - timedelta(days=1)
        quote.save()
        self.client.post(self.url('quotations', quote, 'action/approve/'))
        quote.refresh_from_db()
        self.assertEqual(quote.status, 'draft')

    def test_issued_quote_line_items_protected(self):
        quote = self.quote()
        quote.status = 'sent'
        quote.save()
        item = quote.line_items.get()
        self.client.post(self.url('quotation-line-items', item, 'delete/'))
        self.assertTrue(m.QuotationLineItem.objects.filter(pk=item.pk).exists())
        form = {'quotation': quote.pk, 'description': 'Change', 'quantity': 1, 'unit_price': 99}
        self.assertEqual(self.client.post(self.url('quotation-line-items', item, 'edit/'), form).status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.unit_price, Decimal('100'))

    def test_partial_full_overpayment_and_payment_deletion(self):
        invoice = self.invoice()
        payload = {'invoice': invoice.pk, 'client': self.customer.pk, 'amount': 40, 'paid_at': timezone.localdate().isoformat()}
        self.assertEqual(self.client.post('/dashboard/payments/new/', payload).status_code, 302)
        self.assertEqual(invoice.balance, Decimal('60'))
        self.assertEqual(invoice.payment_status, 'overdue')
        payload['amount'] = 61
        self.assertContains(self.client.post('/dashboard/payments/new/', payload), 'exceeds')
        payload['amount'] = 60
        self.assertEqual(self.client.post('/dashboard/payments/new/', payload).status_code, 302)
        self.assertEqual(invoice.payment_status, 'paid')
        self.client.post(self.url('payments', invoice.payments.get(amount=60), 'delete/'))
        self.assertEqual(invoice.balance, Decimal('60'))

    def test_cancelled_invoice_not_overdue(self):
        invoice = self.invoice()
        invoice.status = 'cancelled'
        invoice.save()
        response = self.client.get('/dashboard/')
        stat = next(s for s in response.context['dashboard_stats'] if s['label'] == 'Overdue Invoices')
        self.assertEqual(stat['value'], 0)

    def test_payment_wrong_client_rejected(self):
        invoice = self.invoice()
        form = _get_form_class(CRUD_RESOURCES['payments'])({'invoice': invoice.pk, 'amount': 10, 'paid_at': timezone.localdate()})
        self.assertFalse(form.is_valid())
        self.assertIn('client', form.errors)

    def test_invoice_total_is_calculated(self):
        payload = {'invoice_number': 'INV-NEW', 'client': self.customer.pk, 'status': 'draft', 'subtotal': 80, 'tax': 20, 'total': 999}
        self.assertEqual(self.client.post('/dashboard/invoices/new/', payload).status_code, 302)
        self.assertEqual(finance_models.Invoice.objects.get(invoice_number='INV-NEW').total, Decimal('100'))

    def test_pdf_documents_and_details(self):
        quote, invoice = self.quote(), self.invoice()
        payment = finance_models.Payment.objects.create(invoice=invoice, client=self.customer, amount=25)
        for resource, obj in [('quotations', quote), ('invoices', invoice), ('payments', payment), ('clients', self.customer)]:
            with self.subTest(resource=resource):
                response = self.client.get(self.url(resource, obj, 'document/'))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF'))
                self.assertEqual(self.client.get(self.url(resource, obj)).status_code, 200)

    def test_kanban_persists_and_rejects_invalid_status(self):
        task = m.ProjectTask.objects.create(project=m.Project.objects.create(name='Project'), title='Task')
        url = self.url('project-tasks', task, 'move/')
        self.assertEqual(self.client.post(url, {'status': 'doing'}).status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.status, 'doing')
        self.assertEqual(self.client.post(url, {'status': 'invalid'}).status_code, 400)

    def test_renewal_invoice_idempotent(self):
        subscription = m.HostingSubscription.objects.create(client=self.customer, service_type='Hosting', expiry_date=timezone.localdate(), renewal_amount=120)
        for _ in range(2):
            self.client.post(self.url('hosting-subscriptions', subscription, 'action/renewal-invoice/'))
        self.assertEqual(subscription.invoices.count(), 1)

    def test_reports_use_receipts_and_balances(self):
        finance_models.Payment.objects.create(invoice=self.invoice(), client=self.customer, amount=40)
        finance_models.Expense.objects.create(title='Expense', amount=10)
        response = self.client.get('/dashboard/reports/')
        metrics = dict(response.context['metrics'])
        self.assertEqual(metrics['Collected revenue'], Decimal('40'))
        self.assertEqual(metrics['Net cash flow'], Decimal('30'))
        self.assertEqual(metrics['Outstanding now'], Decimal('60'))
        self.assertEqual(self.client.post('/dashboard/reports/').status_code, 302)
        self.assertEqual(m.ReportSnapshot.objects.count(), 1)

    def test_search_filter_export_and_pagination(self):
        for i in range(15):
            m.Subscriber.objects.create(email=f'user{i}@example.com', status='active')
        m.Subscriber.objects.create(email='inactive@example.com', status='unsubscribed')
        response = self.client.get('/dashboard/subscribers/?status=active&page=2')
        self.assertEqual(response.context['page_obj'].paginator.count, 15)
        self.assertEqual(len(response.context['rows']), 3)
        response = self.client.get('/dashboard/subscribers/?q=inactive&export=csv')
        self.assertContains(response, 'inactive@example.com')
        self.assertNotContains(response, 'user1@example.com')

    def test_upload_and_protected_download(self):
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            response = self.client.post('/dashboard/client-files/new/', {'client': self.customer.pk, 'title': 'Brief', 'upload': SimpleUploadedFile('brief.pdf', b'%PDF-1.4 test', content_type='application/pdf')})
            self.assertEqual(response.status_code, 302)
            record = m.ClientFile.objects.get()
            response = self.client.get(record.file_url)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF'))
            self.client.force_login(self.staff)
            self.assertEqual(self.client.get(record.file_url).status_code, 404)

    def test_empty_forms_do_not_crash(self):
        for resource in ['quotation-line-items', 'payments', 'invoices', 'leads', 'redirects', 'pipeline-stages']:
            with self.subTest(resource=resource):
                self.assertEqual(self.client.post(f'/dashboard/{resource}/new/', {}).status_code, 200)

    def test_json_capture_validates_email_and_type(self):
        self.assertEqual(self.client.post('/api/leads/', data='[]', content_type='application/json').status_code, 400)
        payload = {'name': 'Person', 'email': 'invalid', 'message': 'Website'}
        self.assertEqual(self.client.post('/api/leads/', payload).status_code, 400)
        payload.update(email='person@example.com', source='quote', utm_campaign='Launch')
        self.assertEqual(self.client.post('/api/leads/', payload).status_code, 200)
        self.assertEqual(m.Enquiry.objects.get().utm_campaign, 'Launch')

    def test_career_and_newsletter_capture(self):
        self.assertEqual(self.client.post('/careers/apply/', {'name': 'Applicant', 'email': 'applicant@example.com', 'position': 'Developer'}).status_code, 200)
        self.assertEqual(CareerApplication.objects.count(), 1)
        for _ in range(2):
            self.assertEqual(self.client.post('/newsletter/subscribe/', {'email': 'reader@example.com'}).status_code, 200)
        self.assertEqual(m.Subscriber.objects.count(), 1)
        self.assertEqual(m.Enquiry.objects.filter(source='newsletter').count(), 1)

    def test_published_content_and_sitemap_exclude_drafts(self):
        published = m.Insight.objects.create(title='Published', status='published', content='Real article')
        draft = m.Insight.objects.create(title='Draft', content='Private draft')
        self.assertContains(self.client.get(f'/insights/{published.slug}/'), 'Real article')
        self.assertEqual(self.client.get(f'/insights/{draft.slug}/').status_code, 404)
        self.assertContains(self.client.get('/sitemap.xml'), published.slug)
        m.SEOSetting.objects.create(path=f'/insights/{published.slug}/', noindex=True)
        self.assertNotContains(self.client.get('/sitemap.xml'), published.slug)

    def test_case_studies_are_public_and_portfolio_redirects(self):
        service = m.ServiceArea.objects.create(name='Web Development', slug='web-development', is_active=True)
        industry = m.Industry.objects.create(name='Healthcare', slug='healthcare')
        technology = case_models.CaseStudyTechnology.objects.create(name='Django', slug='django')
        published = case_models.CaseStudy.objects.create(
            title='Mekmaa Indoor Sports',
            slug='mekmaa-indoor-sports',
            client_name='Mekmaa',
            primary_service=service,
            industry=industry,
            summary='A booking platform built around a real operational problem.',
            overview='Project overview text',
            challenge='Manual bookings slowed the team.',
            solution='LKProfessionals built a digital workflow.',
            results='The team gained a clearer booking process.',
            key_features='Online reservations\nAdmin workflow',
            key_result='Cleaner booking operations',
            status='published',
        )
        published.technologies.add(technology)
        case_models.CaseStudyGalleryImage.objects.create(case_study=published, image='case-studies/gallery/project-1.png', alt_text='Project screen')
        case_models.CaseStudyMetric.objects.create(case_study=published, value='2x', label='Faster admin')
        draft = case_models.CaseStudy.objects.create(title='Private Draft', slug='private-draft')

        listing = self.client.get('/case-studies/')
        self.assertContains(listing, 'Mekmaa Indoor Sports')
        self.assertContains(listing, 'Case Studies')
        self.assertNotContains(listing, 'Private Draft')
        self.assertContains(self.client.get('/case-studies/?service=web-development'), 'Mekmaa Indoor Sports')

        detail = self.client.get(f'/case-studies/{published.slug}/')
        self.assertContains(detail, 'Project overview text')
        self.assertContains(detail, 'Manual bookings slowed the team.')
        self.assertContains(detail, 'Online reservations')
        self.assertContains(detail, 'Django')
        self.assertContains(detail, '2x')
        self.assertContains(detail, 'application/ld+json')
        self.assertEqual(self.client.get(f'/case-studies/{draft.slug}/').status_code, 404)
        self.assertEqual(self.client.get('/case-studies/not-real/').status_code, 404)

        response = self.client.get('/portfolio/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], '/case-studies/')
        response = self.client.get(f'/portfolio/{published.slug}/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], f'/case-studies/{published.slug}/')
        sitemap = self.client.get('/sitemap.xml')
        self.assertContains(sitemap, f'/case-studies/{published.slug}/')
        self.assertNotContains(sitemap, f'/portfolio/{published.slug}/')
        self.assertContains(self.client.get('/partials/header.html'), '/case-studies/')
        self.assertNotContains(self.client.get('/partials/header.html'), 'Project Details')

    def test_case_study_dashboard_resources(self):
        for resource in ['case-studies', 'case-study-technologies', 'case-study-gallery', 'case-study-metrics']:
            with self.subTest(resource=resource):
                self.assertEqual(self.client.get(self.url(resource)).status_code, 200)
                self.assertEqual(self.client.get(self.url(resource, suffix='new/')).status_code, 200)

    def test_direct_image_uploads(self):
        case_study = case_models.CaseStudy.objects.create(title='Upload Case', status='published')
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            self.assertEqual(self.client.post('/dashboard/team-members/new/', {
                'name': 'Team Person',
                'role': 'Developer',
                'email': 'team@example.com',
                'bio': 'Builds useful systems.',
                'display_order': 1,
                'is_active': True,
                'profile_image': uploaded_png('profile.png'),
            }).status_code, 302)
            self.assertTrue(m.TeamMember.objects.get().profile_image.name.startswith('team/'))
            self.assertEqual(self.client.post('/dashboard/insights/new/', {
                'title': 'Image Insight',
                'slug': 'image-insight',
                'summary': 'Direct upload',
                'content': 'Body',
                'status': 'published',
                'is_featured': True,
                'featured_image': uploaded_png('insight.png'),
            }).status_code, 302)
            self.assertTrue(m.Insight.objects.get(slug='image-insight').featured_image.name.startswith('insights/'))
            response = self.client.post(f'/dashboard/case-studies/{case_study.pk}/edit/', {
                'title': case_study.title,
                'slug': case_study.slug,
                'client_name': '',
                'company': '',
                'primary_service': '',
                'related_services': [],
                'industry': '',
                'technologies': [],
                'summary': '',
                'overview': '',
                'challenge': '',
                'solution': '',
                'results': '',
                'key_features': '',
                'key_result': '',
                'featured_image_alt': 'Case image',
                'project_url': '',
                'completion_date': '',
                'status': 'published',
                'is_featured': False,
                'display_order': 0,
                'seo_title': '',
                'seo_description': '',
                'published_at': '',
                'featured_image': uploaded_png('case.png'),
            })
            self.assertEqual(response.status_code, 302)
            case_study.refresh_from_db()
            self.assertTrue(case_study.featured_image.name.startswith('case-studies/'))
            response = self.client.post('/dashboard/case-study-gallery/new/', {
                'case_study': case_study.pk,
                'caption': 'Homepage screen',
                'display_order': 1,
                'is_active': True,
                'image': uploaded_png('screen.png'),
            })
            self.assertEqual(response.status_code, 302)
            image = case_models.CaseStudyGalleryImage.objects.get()
            self.assertTrue(image.image.name.startswith('case-studies/gallery/'))
            self.assertTrue(default_storage.exists(image.image.name))

    def test_redirects_and_cycles(self):
        m.RedirectRule.objects.create(from_path='/old', to_path='/new')
        response = self.client.get('/old')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], '/new')
        m.RedirectRule.objects.create(from_path='/new', to_path='/old')
        self.assertEqual(self.client.get('/old').status_code, 404)

    def test_newsletter_console_backend_cannot_mark_sent(self):
        m.Newsletter.objects.create(subject='Test', content='Body', status='scheduled', scheduled_at=timezone.now())
        with self.assertRaises(CommandError):
            call_command('process_newsletters', stdout=StringIO())
        self.assertEqual(m.Newsletter.objects.get().status, 'scheduled')

    @patch('pages.operations.subprocess.run', side_effect=OSError)
    def test_backup_failure_is_recorded(self, run):
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            self.assertEqual(self.client.post('/dashboard/backups/create/').status_code, 302)
        self.assertEqual(m.BackupRecord.objects.get().status, 'failed')

    def test_logout_requires_post(self):
        self.assertEqual(self.client.get('/logout/').status_code, 405)
        self.assertEqual(self.client.post('/logout/').status_code, 302)
