from xml.etree.ElementTree import Element, SubElement, tostring

from django import forms
from django.core import signing
from django.db import transaction
from django.db.models import Q
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


PUBLISHED_MODELS = {'insights': m.Insight, 'industries': m.Industry, 'markets': m.Market}


def portfolio_redirect(request, slug=None):
    path = '/case-studies/'
    if slug:
        path = f'/case-studies/{slug}/'
    if request.GET:
        return HttpResponsePermanentRedirect(path + '?' + request.GET.urlencode())
    return HttpResponsePermanentRedirect(path)


def about_milestones_redirect(request):
    return HttpResponsePermanentRedirect('/about/')



def insights_index(request):
    records = (
        m.Insight.objects
        .filter(
            status=m.Insight.Status.PUBLISHED,
            published_at__isnull=False,
            published_at__lte=timezone.now(),
        )
        .select_related('category')
        .prefetch_related('tags')
        .order_by('-published_at', '-created_at')
    )

    seo = m.SEOSetting.objects.filter(
        path=request.path
    ).first()

    title = (
        seo.title
        if seo and seo.title
        else 'Insights | LKProfessionals'
    )

    description = (
        seo.description
        if seo and seo.description
        else 'Insights, perspectives, and practical knowledge from LKProfessionals.'
    )

    return render(
        request,
        'site/insights.html',
        {
            'insights': records,
            'title': title,
            'description': description,
            'seo': seo,
            'canonical_path': request.path,
        },
    )


def insight_detail(request, slug):
    insight = get_object_or_404(
        m.Insight.objects
        .filter(
            status=m.Insight.Status.PUBLISHED,
            published_at__isnull=False,
            published_at__lte=timezone.now(),
        )
        .select_related('category')
        .prefetch_related('tags'),
        slug=slug,
    )

    seo = m.SEOSetting.objects.filter(
        path=request.path
    ).first()

    title = (
        seo.title
        if seo and seo.title
        else f'{insight.title} | LKProfessionals'
    )

    description = (
        seo.description
        if seo and seo.description
        else insight.summary
    )

    return render(
        request,
        'site/insight single.html',
        {
            'insight': insight,
            'title': title,
            'description': description,
            'seo': seo,
            'canonical_path': request.path,
        },
    )

def content(request, kind, slug=None):
    model = PUBLISHED_MODELS.get(kind)
    if not model:
        raise Http404
    records = model.objects.filter(status='published') if hasattr(model, 'status') else model.objects.filter(is_active=True)
    if kind == 'insights':
        records = records.filter(published_at__lte=timezone.now())
    obj = get_object_or_404(records, slug=slug) if slug else None
    seo = m.SEOSetting.objects.filter(path=request.path).first()
    title = str(obj) if obj else kind.title()
    description = (seo.description if seo else '') or getattr(obj, 'seo_description', '') or getattr(obj, 'summary', '')
    body = getattr(obj, 'content', '') or getattr(obj, 'body', '') or getattr(obj, 'features', '')
    return render(request, 'site/content.html', {'title': title, 'description': description, 'body': body, 'object': obj, 'records': records if not obj else [], 'kind': kind, 'seo': seo})


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


STATIC_SERVICES = {
    "web-design-development": {
        "template": "site/services/web-design-development.html",
        "title": "Web Design & Development",
    },
    "custom-software-development": {
        "template": "site/services/custom-software-development.html",
        "title": "Custom Software Development",
    },
    "mobile-application-development": {
        "template": "site/services/mobile-application-development.html",
        "title": "Mobile Application Development",
    },
    "it-consultation": {
        "template": "site/services/it-consultation.html",
        "title": "IT Consultation",
    },
    "domain-hosting-maintenance": {
        "template": "site/services/domain-hosting-maintenance.html",
        "title": "Domain, Hosting & Maintenance",
    },
    "digital-marketing": {
        "template": "site/services/digital-marketing.html",
        "title": "Digital Marketing",
    },
    "seo": {
        "template": "site/services/seo.html",
        "title": "SEO",
    },
}


def service_page(request, slug):
    service = STATIC_SERVICES.get(slug)

    if not service:
        raise Http404

    service_area = m.ServiceArea.objects.filter(
        slug=slug,
        is_active=True,
    ).first()

    packages = (
        m.ServicePackage.objects
        .filter(service_area=service_area, is_active=True)
        .order_by("price", "title")
        if service_area
        else m.ServicePackage.objects.none()
    )

    case_studies = CaseStudy.objects.none()

    if service_area:
        case_studies = (
            CaseStudy.objects
            .filter(status=CaseStudy.Status.PUBLISHED)
            .filter(
                Q(published_at__isnull=True) |
                Q(published_at__lte=timezone.now())
            )
            .filter(
                Q(primary_service=service_area) |
                Q(related_services=service_area)
            )
            .select_related(
                "primary_service",
                "industry",
                "company",
            )
            .prefetch_related(
                "technologies",
                "metrics",
            )
            .distinct()
            .order_by(
                "display_order",
                "-completion_date",
                "-created_at",
            )[:3]
        )

    seo = m.SEOSetting.objects.filter(
        path=request.path
    ).first()

    title = (
        seo.title
        if seo and seo.title
        else f'{service["title"]} | LKProfessionals'
    )

    description = (
        seo.description
        if seo and seo.description
        else (
            service_area.summary
            if service_area
            else ""
        )
    )

    return render(
        request,
        service["template"],
        {
            "service": service,
            "service_area": service_area,
            "packages": packages,
            "case_studies": case_studies,
            "title": title,
            "description": description,
            "canonical_path": request.path,
            "seo": seo,
        },
    )
