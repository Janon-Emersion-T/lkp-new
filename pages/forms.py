from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import AccessRole

from .models import Category, Insight, Lead, Newsletter, Portfolio, ServiceArea, Subscriber, Tag


class DashboardModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            widget.attrs.setdefault('class', self._class_for_widget(widget))
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = 'form-check-input'
            elif isinstance(field, forms.DateTimeField):
                field.widget = forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local', 'class': 'form-control'})
            elif isinstance(field, forms.DateField):
                field.widget = forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'})
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('rows', 4)
        if 'file_url' in self.fields:
            self.fields['upload'] = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
            self.fields['file_url'].required = False
        if self._meta.model._meta.model_name in ['quotation', 'invoice', 'quotationlineitem']:
            for name in (['subtotal', 'total'] if self._meta.model._meta.model_name == 'quotation' else ['total']):
                self.fields.pop(name, None)
        if self._meta.model._meta.model_name == 'enquiry':
            self.fields.pop('converted_lead', None)
        if self._meta.model._meta.model_name == 'invoice':
            self.fields['status'].choices = [('draft', 'Draft'), ('sent', 'Sent'), ('cancelled', 'Cancelled')]
        if self._meta.model._meta.model_name == 'newsletter':
            self.fields['status'].choices = [('draft', 'Draft'), ('scheduled', 'Scheduled'), ('archived', 'Archived')]
            self.fields.pop('sent_at', None)

    def clean(self):
        data = super().clean()
        if self._meta.model._meta.model_name == 'newsletter' and data.get('status') == 'scheduled':
            if not data.get('scheduled_at'):
                self.add_error('scheduled_at', 'Choose a scheduled delivery time.')
            if not data.get('content'):
                self.add_error('content', 'Newsletter content is required.')
        if 'slug' in data and not data['slug']:
            base = slugify(data.get('title') or data.get('name') or 'record')
            candidate, suffix = base, 2
            while self._meta.model.objects.filter(slug=candidate).exclude(pk=self.instance.pk).exists():
                candidate, suffix = f'{base}-{suffix}', suffix + 1
            data['slug'] = candidate
        if 'file_url' in self.fields:
            upload = data.get('upload')
            if upload:
                from pathlib import Path
                if upload.size > 20 * 1024 * 1024:
                    self.add_error('upload', 'File must be no larger than 20 MB.')
                if Path(upload.name).suffix.lower() not in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx', '.zip']:
                    self.add_error('upload', 'Unsupported file type.')
            elif not data.get('file_url'):
                self.add_error('file_url', 'Enter a file URL or upload a file.')
        if self._meta.model._meta.model_name == 'quotation' and self.instance.pk:
            subtotal = sum(self.instance.line_items.values_list('total', flat=True))
            if data.get('discount', 0) is not None and data.get('discount', 0) > subtotal:
                self.add_error('discount', 'Discount cannot exceed the line item subtotal.')
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        if obj._meta.model_name == 'invoice':
            obj.total = obj.subtotal + obj.tax
        if self.cleaned_data.get('upload'):
            from django.core.files.storage import default_storage
            from uuid import uuid4
            from pathlib import Path
            upload = self.cleaned_data['upload']
            path = default_storage.save(f'dashboard/{uuid4().hex}{Path(upload.name).suffix.lower()}', upload)
            obj.file_url = f'/dashboard/files/{path}'
        if commit:
            obj.save()
            self.save_m2m()
        return obj

    @staticmethod
    def _class_for_widget(widget):
        if isinstance(widget, forms.Select):
            return 'form-select'
        if isinstance(widget, forms.SelectMultiple):
            return 'form-select'
        if isinstance(widget, forms.Textarea):
            return 'form-control'
        if isinstance(widget, forms.CheckboxInput):
            return 'form-check-input'
        return 'form-control'


class TagForm(DashboardModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'slug', 'is_active']


class CategoryForm(DashboardModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'is_active']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}


class InsightForm(DashboardModelForm):
    class Meta:
        model = Insight
        fields = ['title', 'slug', 'category', 'tags', 'summary', 'content', 'featured_image', 'status', 'is_featured', 'published_at']
        widgets = {
            'tags': forms.SelectMultiple(attrs={'size': 8}),
            'summary': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 10}),
            'featured_image': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
            'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class SubscriberForm(DashboardModelForm):
    class Meta:
        model = Subscriber
        fields = ['email', 'name', 'source', 'status']


class PortfolioForm(DashboardModelForm):
    class Meta:
        model = Portfolio
        fields = [
            'title',
            'slug',
            'client_name',
            'service_area',
            'industry',
            'summary',
            'content',
            'challenge',
            'solution',
            'results',
            'key_features',
            'technology_stack',
            'key_result',
            'image_url',
            'gallery_urls',
            'project_url',
            'seo_title',
            'seo_description',
            'status',
            'is_featured',
            'completed_at',
        ]
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 8}),
            'challenge': forms.Textarea(attrs={'rows': 5}),
            'solution': forms.Textarea(attrs={'rows': 5}),
            'results': forms.Textarea(attrs={'rows': 5}),
            'key_features': forms.Textarea(attrs={'rows': 5}),
            'technology_stack': forms.Textarea(attrs={'rows': 4}),
            'gallery_urls': forms.Textarea(attrs={'rows': 4}),
            'seo_description': forms.Textarea(attrs={'rows': 3}),
            'completed_at': forms.DateInput(attrs={'type': 'date'}),
        }


class NewsletterForm(DashboardModelForm):
    class Meta:
        model = Newsletter
        fields = ['subject', 'preheader', 'content', 'status', 'scheduled_at', 'sent_at']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'sent_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class ServiceAreaForm(DashboardModelForm):
    class Meta:
        model = ServiceArea
        fields = ['name', 'slug', 'summary', 'icon', 'display_order', 'is_active']
        widgets = {'summary': forms.Textarea(attrs={'rows': 4})}


class LeadForm(DashboardModelForm):
    class Meta:
        model = Lead
        fields = [
            'source',
            'company',
            'contact',
            'pipeline_stage',
            'lead_source',
            'name',
            'email',
            'phone',
            'subject',
            'service',
            'message',
            'score',
            'estimated_value',
            'next_follow_up',
            'lost_reason',
            'status',
            'priority',
            'internal_notes',
        ]
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
            'next_follow_up': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'internal_notes': forms.Textarea(attrs={'rows': 5}),
        }


class AccessRoleForm(DashboardModelForm):
    permissions = forms.ModelMultipleChoiceField(queryset=Permission.objects.filter(content_type__app_label__in=['pages', 'case_studies', 'finance', 'team']), required=False)

    class Meta:
        model = AccessRole
        fields = ['name', 'description', 'permissions', 'users', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            codes = [code.split('.')[-1] for code in self.instance.permissions.split()]
            self.initial['permissions'] = Permission.objects.filter(content_type__app_label__in=['pages', 'case_studies', 'finance', 'team'], codename__in=codes)
        self.fields['users'].queryset = get_user_model().objects.filter(is_staff=True, is_active=True)

    def clean_permissions(self):
        return ' '.join(f'{p.content_type.app_label}.{p.codename}' for p in self.cleaned_data['permissions'])


class UserForm(DashboardModelForm):
    password = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False))

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'password']

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.instance.pk and not password:
            raise ValidationError('A password is required for new users.')
        if password:
            validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        old_password = get_user_model().objects.get(pk=self.instance.pk).password if self.instance.pk else ''
        obj = super().save(commit=False)
        if self.cleaned_data['password']:
            obj.set_password(self.cleaned_data['password'])
        else:
            obj.password = old_password
        if commit:
            obj.save()
            self.save_m2m()
        return obj
