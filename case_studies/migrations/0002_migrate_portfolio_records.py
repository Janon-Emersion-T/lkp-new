from django.db import migrations
from django.utils import timezone
from django.utils.text import slugify


def forward(apps, schema_editor):
    Portfolio = apps.get_model('pages', 'Portfolio')
    CaseStudy = apps.get_model('case_studies', 'CaseStudy')
    CaseStudyTechnology = apps.get_model('case_studies', 'CaseStudyTechnology')
    CaseStudyGalleryImage = apps.get_model('case_studies', 'CaseStudyGalleryImage')

    for portfolio in Portfolio.objects.all():
        case_study, created = CaseStudy.objects.get_or_create(
            slug=portfolio.slug,
            defaults={
                'title': portfolio.title,
                'client_name': portfolio.client_name,
                'primary_service_id': portfolio.service_area_id,
                'industry_id': portfolio.industry_id,
                'summary': portfolio.summary,
                'overview': portfolio.content,
                'challenge': portfolio.challenge,
                'solution': portfolio.solution,
                'results': portfolio.results,
                'key_features': portfolio.key_features,
                'key_result': portfolio.key_result,
                'featured_image_url': portfolio.image_url,
                'featured_image_alt': portfolio.title,
                'project_url': portfolio.project_url,
                'completion_date': portfolio.completed_at,
                'status': portfolio.status,
                'is_featured': portfolio.is_featured,
                'seo_title': portfolio.seo_title,
                'seo_description': portfolio.seo_description,
                'published_at': timezone.now() if portfolio.status == 'published' else None,
            },
        )
        if not created:
            continue
        if portfolio.service_area_id:
            case_study.related_services.add(portfolio.service_area_id)
        for index, name in enumerate([line.strip() for line in (portfolio.technology_stack or '').splitlines() if line.strip()]):
            technology, _ = CaseStudyTechnology.objects.get_or_create(
                slug=slugify(name),
                defaults={'name': name, 'is_active': True},
            )
            case_study.technologies.add(technology)
        for index, image_url in enumerate([line.strip() for line in (portfolio.gallery_urls or '').splitlines() if line.strip()]):
            CaseStudyGalleryImage.objects.create(
                case_study=case_study,
                image_url=image_url,
                alt_text=f'{portfolio.title} screenshot {index + 1}',
                display_order=index,
            )


def backward(apps, schema_editor):
    CaseStudy = apps.get_model('case_studies', 'CaseStudy')
    CaseStudy.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('case_studies', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
