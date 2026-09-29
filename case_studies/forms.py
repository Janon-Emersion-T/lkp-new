from django import forms
from django.core.files.storage import default_storage
from pathlib import Path
from uuid import uuid4

from pages.forms import DashboardModelForm

from .models import CaseStudy, CaseStudyGalleryImage, CaseStudyMetric, CaseStudyTechnology


class CaseStudyForm(DashboardModelForm):
    class Meta:
        model = CaseStudy
        fields = [
            'title',
            'slug',
            'client_name',
            'company',
            'primary_service',
            'related_services',
            'industry',
            'technologies',
            'summary',
            'overview',
            'challenge',
            'solution',
            'results',
            'key_features',
            'key_result',
            'featured_image_url',
            'featured_image_alt',
            'project_url',
            'completion_date',
            'status',
            'is_featured',
            'display_order',
            'seo_title',
            'seo_description',
            'published_at',
        ]
        widgets = {
            'related_services': forms.SelectMultiple(attrs={'size': 8}),
            'technologies': forms.SelectMultiple(attrs={'size': 8}),
            'summary': forms.Textarea(attrs={'rows': 3}),
            'overview': forms.Textarea(attrs={'rows': 8}),
            'challenge': forms.Textarea(attrs={'rows': 5}),
            'solution': forms.Textarea(attrs={'rows': 5}),
            'results': forms.Textarea(attrs={'rows': 5}),
            'key_features': forms.Textarea(attrs={'rows': 5}),
            'seo_description': forms.Textarea(attrs={'rows': 3}),
            'completion_date': forms.DateInput(attrs={'type': 'date'}),
            'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class CaseStudyTechnologyForm(DashboardModelForm):
    class Meta:
        model = CaseStudyTechnology
        fields = ['name', 'slug', 'icon', 'summary', 'is_active']
        widgets = {'summary': forms.Textarea(attrs={'rows': 4})}


class CaseStudyMetricForm(DashboardModelForm):
    class Meta:
        model = CaseStudyMetric
        fields = ['case_study', 'label', 'value', 'note', 'display_order']


class CaseStudyGalleryImageForm(DashboardModelForm):
    upload = forms.FileField(
        required=False,
        help_text='Upload JPG, PNG, WebP, or GIF up to 20 MB. You can also paste an image URL instead.',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/webp,image/gif'}),
    )

    class Meta:
        model = CaseStudyGalleryImage
        fields = ['case_study', 'image_url', 'alt_text', 'caption', 'display_order', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image_url'].required = False

    def clean(self):
        data = super().clean()
        upload = data.get('upload')
        if upload:
            suffix = Path(upload.name).suffix.lower()
            if upload.size > 20 * 1024 * 1024:
                self.add_error('upload', 'Image must be no larger than 20 MB.')
            if suffix not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                self.add_error('upload', 'Upload a JPG, PNG, WebP, or GIF image.')
        elif not data.get('image_url'):
            self.add_error('image_url', 'Enter an image URL or upload an image.')
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        upload = self.cleaned_data.get('upload')
        if upload:
            suffix = Path(upload.name).suffix.lower()
            path = default_storage.save(f'dashboard/case-studies/gallery/{uuid4().hex}{suffix}', upload)
            obj.image_url = f'/dashboard/files/{path}'
            if not obj.alt_text:
                obj.alt_text = obj.caption or obj.case_study.title
        if commit:
            obj.save()
            self.save_m2m()
        return obj
