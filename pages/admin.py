from django.contrib import admin
from django.apps import apps

from .models import Category, Insight, Lead, Newsletter, Portfolio, ServiceArea, Subscriber, Tag


@admin.register(Tag, Category, ServiceArea)
class SluggedAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')


@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'is_featured', 'published_at', 'updated_at')
    list_filter = ('status', 'is_featured', 'category', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'summary', 'content')
    filter_horizontal = ('tags',)


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'status', 'source', 'created_at')
    list_filter = ('status', 'source')
    search_fields = ('email', 'name')


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('title', 'client_name', 'service_area', 'status', 'is_featured', 'completed_at')
    list_filter = ('status', 'is_featured', 'service_area')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'client_name', 'summary', 'content')


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('subject', 'status', 'scheduled_at', 'sent_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('subject', 'preheader', 'content')


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'source', 'service', 'status', 'priority', 'created_at')
    list_filter = ('source', 'status', 'priority')
    search_fields = ('name', 'email', 'phone', 'subject', 'service', 'message')


for model in apps.get_app_config('pages').get_models():
    if model in admin.site._registry:
        continue

    admin.site.register(
        model,
        type(
            f'{model.__name__}Admin',
            (admin.ModelAdmin,),
            {
                'list_display': ('__str__', 'created_at', 'updated_at') if hasattr(model, 'created_at') else ('__str__',),
                'search_fields': ('id',),
            },
        ),
    )
