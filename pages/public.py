from pathlib import Path
from uuid import uuid4
from xml.etree.ElementTree import Element, SubElement, tostring

from django import forms
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponsePermanentRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from case_studies.models import CaseStudy
from . import models as m


class SubscriptionForm(forms.Form):
    email = forms.EmailField(max_length=254)


@require_POST
def subscribe(request):
    form = SubscriptionForm(request.POST)
    if not form.is_valid():
        return render(request, 'site/submission.html', {'title': 'Invalid email', 'message': 'Please enter a valid email address.'}, status=400)
    email = form.cleaned_data['email'].lower()
    with transaction.atomic():
        subscriber, created = m.Subscriber.objects.get_or_create(email=email, defaults={'source': 'website'})
        if created:
            m.Enquiry.objects.create(source='newsletter', name=email, email=email, message='Newsletter subscription')
    return render(request, 'site/submission.html', {'title': 'Thank you', 'message': 'Your subscription request has been received.'})


def unsubscribe(request, token):
    try:
        pk = signing.loads(token, salt='newsletter-unsubscribe')
    except signing.BadSignature:
        raise Http404
    subscriber = get_object_or_404(m.Subscriber, pk=pk)
    if request.method == 'POST':
        subscriber.status = 'unsubscribed'
        subscriber.save()
        return render(request, 'site/submission.html', {'title': 'Unsubscribed', 'message': 'You will no longer receive newsletters.'})
    return render(request, 'site/submission.html', {'title': 'Unsubscribe', 'message': 'Confirm that you want to stop receiving newsletters.', 'confirm': True})


@require_POST
def apply_for_job(request):
    name, email = request.POST.get('name', '').strip(), request.POST.get('email', '').strip()
    application = m.CareerApplication(name=name, email=email, phone=request.POST.get('phone', ''), position=request.POST.get('position', '') or 'General application', message=request.POST.get('message', ''))
    upload = request.FILES.get('resume')
    try:
        application.full_clean()
        if upload:
            if Path(upload.name).suffix.lower() not in ['.pdf', '.docx'] or upload.size > 5 * 1024 * 1024:
                raise ValidationError('Upload a PDF or DOCX no larger than 5 MB.')
            path = default_storage.save(f'dashboard/resumes/{uuid4().hex}{Path(upload.name).suffix.lower()}', upload)
            application.resume_url = f'/dashboard/files/{path}'
        with transaction.atomic():
            application.save()
            m.Enquiry.objects.create(source='career', name=name, email=email, phone=application.phone, subject=application.position, message=application.message or 'Career application')
    except ValidationError as error:
        return render(request, 'site/submission.html', {'title': 'Application needs attention', 'message': '; '.join(error.messages)}, status=400)
    return render(request, 'site/submission.html', {'title': 'Application received', 'message': 'Thank you. Our team will review your application.'})


PUBLISHED_MODELS = {'insights': m.Insight, 'pages': m.CMSPage, 'services': m.ServicePackage, 'industries': m.Industry, 'markets': m.Market}


def portfolio_redirect(request, slug=None):
    path = '/case-studies/'
    if slug:
        path = f'/case-studies/{slug}/'
    if request.GET:
        return HttpResponsePermanentRedirect(path + '?' + request.GET.urlencode())
    return HttpResponsePermanentRedirect(path)


def content(request, kind, slug=None):
    model = PUBLISHED_MODELS.get(kind)
    if not model:
        raise Http404
    records = model.objects.filter(status='published') if hasattr(model, 'status') else model.objects.filter(is_active=True)
    if kind == 'insights':
        records = records.filter(published_at__lte=timezone.now())
    obj = get_object_or_404(records, slug=slug) if slug else None
    seo = m.SEOSetting.objects.filter(path=request.path).first()
    sections = obj.sections.filter(is_active=True) if kind == 'pages' and obj else []
    title = str(obj) if obj else kind.title()
    description = (seo.description if seo else '') or getattr(obj, 'seo_description', '') or getattr(obj, 'summary', '')
    body = getattr(obj, 'content', '') or getattr(obj, 'body', '') or getattr(obj, 'features', '')
    return render(request, 'site/content.html', {'title': title, 'description': description, 'body': body, 'object': obj, 'records': records if not obj else [], 'kind': kind, 'seo': seo, 'sections': sections})


def sitemap(request):
    root = Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    hidden = set(m.SEOSetting.objects.filter(noindex=True).values_list('path', flat=True))
    index_paths = ['/', '/case-studies/']
    for path in index_paths:
        if path not in hidden:
            url = SubElement(root, 'url')
            SubElement(url, 'loc').text = request.build_absolute_uri(path)
    for obj in CaseStudy.objects.filter(status=CaseStudy.Status.PUBLISHED):
        path = f'/case-studies/{obj.slug}/'
        if path not in hidden:
            url = SubElement(root, 'url')
            SubElement(url, 'loc').text = request.build_absolute_uri(path)
            SubElement(url, 'lastmod').text = obj.updated_at.date().isoformat()
    for kind, model in PUBLISHED_MODELS.items():
        records = model.objects.filter(status='published') if hasattr(model, 'status') else model.objects.filter(is_active=True)
        if kind == 'insights':
            records = records.filter(published_at__lte=timezone.now())
        for obj in records:
            path = f'/{kind}/{obj.slug}/'
            if path not in hidden:
                url = SubElement(root, 'url')
                SubElement(url, 'loc').text = request.build_absolute_uri(path)
                SubElement(url, 'lastmod').text = obj.updated_at.date().isoformat()
    return HttpResponse(tostring(root, encoding='utf-8', xml_declaration=True), content_type='application/xml')


class RedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ['GET', 'HEAD'] and not request.path.startswith(('/dashboard/', '/admin/', '/api/', '/assets/', '/static/', '/login/', '/logout/')):
            path, visited, status = request.path, set(), 301
            while path not in visited:
                visited.add(path)
                rule = m.RedirectRule.objects.filter(from_path=path, is_active=True).first()
                if not rule:
                    if path != request.path:
                        response = HttpResponse(status=status)
                        response['Location'] = path
                        return response
                    break
                if not rule.to_path.startswith('/') or rule.to_path.startswith('//'):
                    break
                path, status = rule.to_path, rule.status_code
        return self.get_response(request)
