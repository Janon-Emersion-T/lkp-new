import json

from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from django.utils import timezone

from pages import models as page_models

from .models import CaseStudy


def published_case_studies():
    return (
        CaseStudy.objects.filter(status=CaseStudy.Status.PUBLISHED)
        .filter(Q(published_at__isnull=True) | Q(published_at__lte=timezone.now()))
        .select_related('primary_service', 'industry', 'company')
        .prefetch_related('related_services', 'technologies', 'metrics', 'gallery')
    )


def _lines(value):
    return [line.strip() for line in (value or '').splitlines() if line.strip()]


def case_studies(request):
    records = published_case_studies().distinct()
    service_slug = request.GET.get('service', '').strip()
    if service_slug:
        records = records.filter(primary_service__slug=service_slug)
    filters = page_models.ServiceArea.objects.filter(is_active=True, case_studies__status=CaseStudy.Status.PUBLISHED).distinct().order_by('display_order', 'name')
    seo = page_models.SEOSetting.objects.filter(path='/case-studies/').first()
    description = (seo.description if seo else '') or 'Case studies from LKProfessionals across strategy, engineering, SEO, marketing and automation.'
    return render(request, 'site/case_studies.html', {
        'title': (seo.title if seo and seo.title else 'Case Studies | LKProfessionals'),
        'description': description,
        'canonical_path': '/case-studies/',
        'records': records,
        'filters': filters,
        'active_service': service_slug,
        'seo': seo,
    })


def case_study_detail(request, slug):
    obj = get_object_or_404(published_case_studies().distinct(), slug=slug)
    related = published_case_studies().exclude(pk=obj.pk).distinct()
    if obj.primary_service_id:
        related = related.filter(primary_service=obj.primary_service)
    related = related[:3]
    seo = page_models.SEOSetting.objects.filter(path=request.path).first()
    title = (seo.title if seo and seo.title else obj.seo_title or f'{obj.title} Case Study | LKProfessionals')
    description = (seo.description if seo else '') or obj.seo_description or obj.summary
    schema = {
        '@context': 'https://schema.org',
        '@type': 'CreativeWork',
        'name': obj.title,
        'description': description,
        'url': request.build_absolute_uri(request.path),
        'publisher': {'@type': 'Organization', 'name': 'LKProfessionals'},
    }
    if obj.client_name:
        schema['about'] = obj.client_name
    if obj.featured_image:
        schema['image'] = request.build_absolute_uri(obj.featured_image.url)
    return render(request, 'site/case_study_detail.html', {
        'object': obj,
        'title': title,
        'description': description,
        'canonical_path': obj.public_url,
        'features': _lines(obj.key_features),
        'stack': obj.technologies.filter(is_active=True),
        'gallery': obj.gallery.filter(is_active=True),
        'metrics': obj.metrics.all(),
        'related': related,
        'schema_json': json.dumps(schema),
        'seo': seo,
    })
