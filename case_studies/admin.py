from django.contrib import admin

from .models import CaseStudy, CaseStudyGalleryImage, CaseStudyMetric, CaseStudyTechnology


class CaseStudyGalleryInline(admin.TabularInline):
    model = CaseStudyGalleryImage
    extra = 0


class CaseStudyMetricInline(admin.TabularInline):
    model = CaseStudyMetric
    extra = 0


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ('title', 'client_name', 'primary_service', 'industry', 'status', 'is_featured', 'completion_date')
    list_filter = ('status', 'is_featured', 'primary_service', 'industry')
    search_fields = ('title', 'client_name', 'summary', 'overview')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('related_services', 'technologies')
    inlines = [CaseStudyMetricInline, CaseStudyGalleryInline]


@admin.register(CaseStudyTechnology)
class CaseStudyTechnologyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'updated_at')
    search_fields = ('name', 'summary')
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(CaseStudyMetric)
admin.site.register(CaseStudyGalleryImage)
