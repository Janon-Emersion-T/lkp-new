from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from pages.validators import validate_image_upload


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CaseStudyTechnology(TimeStampedModel):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    icon = models.CharField(max_length=80, blank=True)
    summary = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Case Study Technology'
        verbose_name_plural = 'Case Study Technologies'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CaseStudy(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    client_name = models.CharField(max_length=180, blank=True)
    company = models.ForeignKey('pages.Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='case_studies')
    primary_service = models.ForeignKey('pages.ServiceArea', on_delete=models.SET_NULL, null=True, blank=True, related_name='case_studies')
    related_services = models.ManyToManyField('pages.ServiceArea', blank=True, related_name='related_case_studies')
    industry = models.ForeignKey('pages.Industry', on_delete=models.SET_NULL, null=True, blank=True, related_name='case_studies')
    technologies = models.ManyToManyField(CaseStudyTechnology, blank=True, related_name='case_studies')
    summary = models.TextField(blank=True)
    overview = models.TextField(blank=True)
    challenge = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    results = models.TextField(blank=True)
    key_features = models.TextField(blank=True, help_text='One feature per line')
    key_result = models.CharField(max_length=260, blank=True)
    featured_image = models.ImageField(upload_to='case-studies/', blank=True, null=True, validators=[validate_image_upload])
    featured_image_alt = models.CharField(max_length=220, blank=True)
    project_url = models.URLField(blank=True)
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    seo_title = models.CharField(max_length=260, blank=True)
    seo_description = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['display_order', '-completion_date', '-created_at']
        verbose_name = 'Case Study'
        verbose_name_plural = 'Case Studies'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def public_url(self):
        return f'/case-studies/{self.slug}/'


class CaseStudyMetric(TimeStampedModel):
    case_study = models.ForeignKey(CaseStudy, on_delete=models.CASCADE, related_name='metrics')
    label = models.CharField(max_length=120)
    value = models.CharField(max_length=120)
    note = models.CharField(max_length=220, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'label']
        verbose_name = 'Case Study Metric'
        verbose_name_plural = 'Case Study Metrics'

    def __str__(self):
        return f'{self.value} {self.label}'


class CaseStudyGalleryImage(TimeStampedModel):
    case_study = models.ForeignKey(CaseStudy, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='case-studies/gallery/', blank=True, null=True, validators=[validate_image_upload])
    alt_text = models.CharField(max_length=220, blank=True)
    caption = models.CharField(max_length=260, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'created_at']
        verbose_name = 'Case Study Gallery Image'
        verbose_name_plural = 'Case Study Gallery'

    def __str__(self):
        return self.caption or self.alt_text or str(self.image)
