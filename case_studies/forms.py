from django import forms

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
            'featured_image',
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
    class Meta:
        model = CaseStudyGalleryImage
        fields = ['case_study', 'image', 'alt_text', 'caption', 'display_order', 'is_active']
        widgets = {'image': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'})}

    def clean(self):
        data = super().clean()
        if not data.get('image') and not self.instance.pk:
            self.add_error('image', 'Upload a gallery image.')
        return data
