import json
from datetime import timedelta

from django.contrib import messages
from django.http import Http404
from django.contrib.auth import logout, get_user_model
from .access import staff_required as login_required, require_permission, allowed, audit
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.forms import modelform_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from case_studies.forms import CaseStudyForm, CaseStudyGalleryImageForm, CaseStudyMetricForm, CaseStudyTechnologyForm
from case_studies.models import CaseStudy, CaseStudyGalleryImage, CaseStudyMetric, CaseStudyTechnology
from .forms import CategoryForm, DashboardModelForm, InsightForm, LeadForm, NewsletterForm, PortfolioForm, ServiceAreaForm, SubscriberForm, TagForm, AccessRoleForm, UserForm
from .models import (
    AuditLog,
    AccessRole,
    APIKeyCredential,
    BackupRecord,
    Campaign,
    CareerApplication,
    Category,
    Client,
    ClientCommunication,
    ClientCredential,
    ClientFile,
    CMSPage,
    Company,
    Contact,
    Employee,
    Enquiry,
    Expense,
    FAQItem,
    FollowUp,
    GlobalSetting,
    HostingSubscription,
    Industry,
    Insight,
    IntegrationSetting,
    Invoice,
    Lead,
    LeadSource,
    Market,
    MediaAsset,
    NavigationItem,
    Newsletter,
    NotificationRule,
    Payment,
    PipelineStage,
    Portfolio,
    Project,
    ProjectFile,
    ProjectMilestone,
    ProjectTask,
    Quotation,
    QuotationLineItem,
    RedirectRule,
    ReportSnapshot,
    SEOSetting,
    ServiceArea,
    ServicePackage,
    Subscriber,
    Tag,
    TeamMember,
    Testimonial,
    WebsiteSection,
    SupportTicket,
    NewsletterDelivery,
)


DASHBOARD_NAV = [
    {
        'label': 'Command Center',
        'icon': 'ti-layout-dashboard',
        'resource': 'dashboard',
        'url_name': 'dashboard',
    },
    {
        'label': 'CRM & Sales',
        'icon': 'ti-target-arrow',
        'children': [
            {'label': 'Leads', 'resource': 'leads'},
            {'label': 'Companies', 'resource': 'companies'},
            {'label': 'Contacts', 'resource': 'contacts'},
            {'label': 'Pipeline Stages', 'resource': 'pipeline-stages'},
            {'label': 'Lead Sources', 'resource': 'lead-sources'},
            {'label': 'Follow-ups', 'resource': 'follow-ups'},
        ],
    },
    {
        'label': 'Clients',
        'icon': 'ti-building-community',
        'children': [
            {'label': 'Clients', 'resource': 'clients'},
            {'label': 'Contacts', 'resource': 'contacts'},
            {'label': 'Communications', 'resource': 'client-communications'},
            {'label': 'Files', 'resource': 'client-files'},
            {'label': 'Credentials', 'resource': 'client-credentials'},
            {'label': 'Support Tickets', 'resource': 'support-tickets'},
        ],
    },
    {
        'label': 'Quotations & Proposals',
        'icon': 'ti-file-dollar',
        'children': [
            {'label': 'Quotations', 'resource': 'quotations'},
            {'label': 'Line Items', 'resource': 'quotation-line-items'},
            {'label': 'Packages', 'resource': 'service-packages'},
        ],
    },
    {
        'label': 'Projects',
        'icon': 'ti-kanban',
        'children': [
            {'label': 'Projects', 'resource': 'projects'},
            {'label': 'Milestones', 'resource': 'project-milestones'},
            {'label': 'Tasks', 'resource': 'project-tasks'},
            {'label': 'Files', 'resource': 'project-files'},
        ],
    },
    {
        'label': 'Finance',
        'icon': 'ti-report-money',
        'children': [
            {'label': 'Invoices', 'resource': 'invoices'},
            {'label': 'Payments', 'resource': 'payments'},
            {'label': 'Expenses', 'resource': 'expenses'},
        ],
    },
    {
        'label': 'Services & Packages',
        'icon': 'ti-package',
        'children': [
            {'label': 'Service Areas', 'resource': 'service-areas'},
            {'label': 'Packages', 'resource': 'service-packages'},
            {'label': 'FAQs', 'resource': 'faqs'},
        ],
    },
    {
        'label': 'Website CMS',
        'icon': 'ti-browser',
        'children': [
            {'label': 'Pages', 'resource': 'cms-pages'},
            {'label': 'Sections', 'resource': 'website-sections'},
            {'label': 'Navigation/Footer', 'resource': 'navigation-items'},
            {'label': 'Insights', 'resource': 'insights'},
            {'label': 'Industries', 'resource': 'industries'},
            {'label': 'Markets', 'resource': 'markets'},
            {'label': 'Testimonials', 'resource': 'testimonials'},
            {'label': 'Team', 'resource': 'team-members'},
            {'label': 'Media Library', 'resource': 'media-assets'},
            {'label': 'Global Settings', 'resource': 'global-settings'},
        ],
    },
    {
        'label': 'Case Studies',
        'icon': 'ti-briefcase',
        'children': [
            {'label': 'Case Studies', 'resource': 'case-studies'},
            {'label': 'Technologies', 'resource': 'case-study-technologies'},
            {'label': 'Gallery', 'resource': 'case-study-gallery'},
            {'label': 'Metrics', 'resource': 'case-study-metrics'},
        ],
    },
    {
        'label': 'Insights',
        'icon': 'ti-news',
        'children': [
            {'label': 'Tags', 'resource': 'tags'},
            {'label': 'Category', 'resource': 'categories'},
            {'label': 'Insights', 'resource': 'insights'},
        ],
    },
    {
        'label': 'Marketing & SEO',
        'icon': 'ti-speakerphone',
        'children': [
            {'label': 'Campaigns', 'resource': 'campaigns'},
            {'label': 'SEO Metadata', 'resource': 'seo-settings'},
            {'label': 'Redirects', 'resource': 'redirects'},
            {'label': 'Subscribers', 'resource': 'subscribers'},
            {'label': 'Newsletters', 'resource': 'newsletters'},
            {'label': 'Newsletter Deliveries', 'resource': 'newsletter-deliveries'},
            {'label': 'Lead Sources', 'resource': 'lead-sources'},
        ],
    },
    {
        'label': 'Enquiries',
        'icon': 'ti-inbox',
        'children': [
            {'label': 'Website Enquiries', 'resource': 'enquiries'},
            {'label': 'Career Applications', 'resource': 'career-applications'},
            {'label': 'Subscribers', 'resource': 'subscribers'},
        ],
    },
    {
        'label': 'HR & Team',
        'icon': 'ti-users-group',
        'children': [
            {'label': 'Employees', 'resource': 'employees'},
            {'label': 'Applications', 'resource': 'career-applications'},
            {'label': 'Tasks', 'resource': 'project-tasks'},
        ],
    },
    {
        'label': 'Hosting & Subscriptions',
        'icon': 'ti-server',
        'children': [
            {'label': 'Hosting & Renewals', 'resource': 'hosting-subscriptions'},
        ],
    },
    {
        'label': 'Reports',
        'icon': 'ti-chart-bar',
        'children': [
            {'label': 'Report Snapshots', 'resource': 'report-snapshots'},
            {'label': 'Live Reports', 'resource': 'reports', 'url_name': 'dashboard_reports'},
        ],
    },
    {
        'label': 'Administration',
        'icon': 'ti-shield-lock',
        'children': [
            {'label': 'Roles / RBAC', 'resource': 'access-roles'},
            {'label': 'User Accounts', 'resource': 'users'},
            {'label': 'Audit Logs', 'resource': 'audit-logs'},
            {'label': 'Notification Rules', 'resource': 'notification-rules'},
            {'label': 'Integrations', 'resource': 'integrations'},
            {'label': 'API Keys', 'resource': 'api-keys'},
            {'label': 'Backups', 'resource': 'backups'},
            {'label': 'System Settings', 'resource': 'global-settings'},
        ],
    },
]


def resource(model, title, singular, description, columns, search=None, fields='__all__', form=None):
    config = {
        'model': model,
        'title': title,
        'singular': singular,
        'description': description,
        'columns': columns,
        'search': search or [],
        'fields': fields,
    }
    if form:
        config['form'] = form
    return config


CRUD_RESOURCES = {
    'support-tickets': resource(SupportTicket, 'Support Tickets', 'Support Ticket', 'Client support requests and resolution history.', [('subject', 'Subject'), ('client', 'Client'), ('status', 'Status'), ('assigned_to', 'Assigned')], ['subject', 'message', 'client__name']),
    'newsletter-deliveries': resource(NewsletterDelivery, 'Newsletter Deliveries', 'Delivery', 'Delivery outcomes per subscriber.', [('newsletter', 'Newsletter'), ('subscriber', 'Subscriber'), ('status', 'Status'), ('sent_at', 'Sent')], ['subscriber__email', 'newsletter__subject']),
    'users': resource(get_user_model(), 'User Accounts', 'User', 'Team accounts and dashboard access.', [('username', 'Username'), ('email', 'Email'), ('is_staff', 'Staff'), ('is_active', 'Active')], ['username', 'email'], form=UserForm),
    'tags': resource(Tag, 'Tags', 'Tag', 'Organize insights with reusable tags.', [('name', 'Name'), ('slug', 'Slug'), ('is_active', 'Active'), ('updated_at', 'Updated')], ['name', 'slug'], form=TagForm),
    'categories': resource(Category, 'Categories', 'Category', 'Group insights into clear editorial categories.', [('name', 'Name'), ('slug', 'Slug'), ('is_active', 'Active'), ('updated_at', 'Updated')], ['name', 'slug', 'description'], form=CategoryForm),
    'insights': resource(Insight, 'Insights', 'Insight', 'Create and manage articles, updates, and thought leadership.', [('title', 'Title'), ('category', 'Category'), ('status', 'Status'), ('is_featured', 'Featured'), ('published_at', 'Published')], ['title', 'summary', 'content'], form=InsightForm),
    'subscribers': resource(Subscriber, 'Subscribers', 'Subscriber', 'Manage newsletter and campaign subscribers.', [('email', 'Email'), ('name', 'Name'), ('status', 'Status'), ('source', 'Source'), ('created_at', 'Joined')], ['email', 'name', 'source'], form=SubscriberForm),
    'case-studies': resource(CaseStudy, 'Case Studies', 'Case Study', 'Publish polished client success stories with services, technology, results, SEO, gallery and proof points.', [('title', 'Title'), ('client_name', 'Client'), ('primary_service', 'Service'), ('industry', 'Industry'), ('status', 'Status'), ('completion_date', 'Completed')], ['title', 'client_name', 'summary', 'overview', 'challenge', 'solution', 'results'], form=CaseStudyForm),
    'case-study-technologies': resource(CaseStudyTechnology, 'Case Study Technologies', 'Technology', 'Reusable technologies, platforms, and capabilities used in case studies.', [('name', 'Name'), ('slug', 'Slug'), ('is_active', 'Active'), ('updated_at', 'Updated')], ['name', 'slug', 'summary'], form=CaseStudyTechnologyForm),
    'case-study-gallery': resource(CaseStudyGalleryImage, 'Case Study Gallery', 'Gallery Image', 'Screenshots, visual proof, and project images connected to case studies.', [('case_study', 'Case Study'), ('caption', 'Caption'), ('image_url', 'Image'), ('display_order', 'Order'), ('is_active', 'Active')], ['caption', 'alt_text', 'image_url', 'case_study__title'], form=CaseStudyGalleryImageForm),
    'case-study-metrics': resource(CaseStudyMetric, 'Case Study Metrics', 'Metric', 'Result cards and supporting proof points for case studies.', [('case_study', 'Case Study'), ('value', 'Value'), ('label', 'Label'), ('display_order', 'Order')], ['label', 'value', 'note', 'case_study__title'], form=CaseStudyMetricForm),
    'portfolios': resource(Portfolio, 'Portfolios', 'Portfolio Item', 'Showcase client work, case studies, and delivery outcomes.', [('title', 'Title'), ('client_name', 'Client'), ('service_area', 'Service Area'), ('status', 'Status'), ('completed_at', 'Completed')], ['title', 'client_name', 'summary', 'content'], form=PortfolioForm),
    'newsletters': resource(Newsletter, 'Newsletters', 'Newsletter', 'Draft, schedule, and track newsletter content.', [('subject', 'Subject'), ('status', 'Status'), ('scheduled_at', 'Scheduled'), ('sent_at', 'Sent'), ('created_at', 'Created')], ['subject', 'preheader', 'content'], form=NewsletterForm),
    'service-areas': resource(ServiceArea, 'Service Areas', 'Service Area', 'Maintain services and practice areas shown across the website.', [('name', 'Name'), ('display_order', 'Order'), ('is_active', 'Active'), ('updated_at', 'Updated')], ['name', 'summary', 'slug'], form=ServiceAreaForm),
    'enquiries': resource(Enquiry, 'Website Enquiries', 'Enquiry', 'Contact, quote, consultation, career, and newsletter submissions arrive here before qualification.', [('name', 'Name'), ('email', 'Email'), ('source', 'Source'), ('status', 'Status'), ('converted_lead', 'CRM Lead'), ('created_at', 'Received')], ['name', 'email', 'phone', 'subject', 'service', 'message']),
    'leads': resource(Lead, 'CRM Leads', 'Lead', 'Manage qualified sales opportunities, scoring, follow-ups, quotations, and conversion tracking.', [('name', 'Name'), ('email', 'Email'), ('pipeline_stage', 'Stage'), ('estimated_value', 'Value'), ('score', 'Score'), ('status', 'Status')], ['name', 'email', 'phone', 'subject', 'service', 'message'], form=LeadForm),
    'companies': resource(Company, 'Companies', 'Company', 'Company-level CRM records for prospects, clients, and partners.', [('name', 'Name'), ('industry', 'Industry'), ('email', 'Email'), ('phone', 'Phone'), ('status', 'Status')], ['name', 'industry', 'email', 'phone']),
    'contacts': resource(Contact, 'Contacts', 'Contact', 'People associated with companies, clients, opportunities, and projects.', [('name', 'Name'), ('company', 'Company'), ('email', 'Email'), ('phone', 'Phone'), ('is_primary', 'Primary')], ['name', 'email', 'phone', 'job_title']),
    'pipeline-stages': resource(PipelineStage, 'Pipeline Stages', 'Pipeline Stage', 'Sales stage definitions with probability and order.', [('name', 'Name'), ('probability', 'Probability'), ('display_order', 'Order'), ('is_active', 'Active')], ['name', 'slug']),
    'lead-sources': resource(LeadSource, 'Lead Sources', 'Lead Source', 'Track lead source, UTM origin, and attribution quality.', [('name', 'Name'), ('utm_source', 'UTM Source'), ('is_active', 'Active'), ('updated_at', 'Updated')], ['name', 'utm_source', 'description']),
    'follow-ups': resource(FollowUp, 'Follow-ups', 'Follow-up', 'Scheduled lead follow-ups and sales reminders.', [('lead', 'Lead'), ('due_at', 'Due'), ('status', 'Status'), ('completed_at', 'Completed')], ['notes', 'lead__name', 'lead__email']),
    'clients': resource(Client, 'Clients', 'Client', 'Complete client profiles with account notes, billing information, and relationships.', [('name', 'Name'), ('email', 'Email'), ('phone', 'Phone'), ('status', 'Status'), ('updated_at', 'Updated')], ['name', 'email', 'phone', 'account_notes']),
    'client-communications': resource(ClientCommunication, 'Client Communications', 'Communication', 'Communication timeline covering calls, email, meetings, WhatsApp, support notes, and client history.', [('client', 'Client'), ('communication_type', 'Type'), ('subject', 'Subject'), ('happened_at', 'When')], ['subject', 'notes', 'client__name']),
    'client-files': resource(ClientFile, 'Client Files', 'Client File', 'Client documents, references, assets, and support files.', [('client', 'Client'), ('title', 'Title'), ('category', 'Category'), ('updated_at', 'Updated')], ['title', 'file_url', 'category', 'notes']),
    'client-credentials': resource(ClientCredential, 'Client Credentials / References', 'Credential Reference', 'Credential references and sensitive-access notes without storing raw secrets in the dashboard.', [('client', 'Client'), ('label', 'Label'), ('reference', 'Reference'), ('updated_at', 'Updated')], ['label', 'reference', 'secret_hint', 'notes']),
    'quotations': resource(Quotation, 'Quotations & Proposals', 'Quotation', 'Reusable proposals with revisions, expiry, approval status, discounts, and taxes.', [('quote_number', 'Quote #'), ('title', 'Title'), ('client', 'Client'), ('status', 'Status'), ('total', 'Total'), ('valid_until', 'Expires')], ['quote_number', 'title', 'notes']),
    'quotation-line-items': resource(QuotationLineItem, 'Quotation Line Items', 'Line Item', 'Custom proposal services, packages, and pricing rows.', [('quotation', 'Quotation'), ('description', 'Description'), ('quantity', 'Qty'), ('unit_price', 'Unit'), ('total', 'Total')], ['description']),
    'projects': resource(Project, 'Projects', 'Project', 'Project overview, requirements, deployment information, budget, profitability, and status.', [('name', 'Project'), ('client', 'Client'), ('status', 'Status'), ('budget', 'Budget'), ('due_date', 'Deadline')], ['name', 'requirements', 'deployment_info']),
    'project-milestones': resource(ProjectMilestone, 'Milestones', 'Milestone', 'Project milestones and delivery checkpoints.', [('project', 'Project'), ('title', 'Title'), ('due_date', 'Due'), ('is_complete', 'Complete')], ['title', 'notes']),
    'project-tasks': resource(ProjectTask, 'Tasks / Kanban', 'Task', 'Kanban-ready project tasks with assignment and deadlines.', [('project', 'Project'), ('title', 'Task'), ('status', 'Status'), ('assigned_to', 'Assigned'), ('due_date', 'Due')], ['title', 'assigned_to', 'notes']),
    'project-files': resource(ProjectFile, 'Project Files', 'Project File', 'Project assets, requirements, deliverables, and deployment files.', [('project', 'Project'), ('title', 'Title'), ('category', 'Category'), ('updated_at', 'Updated')], ['title', 'file_url', 'category', 'notes']),
    'invoices': resource(Invoice, 'Invoices', 'Invoice', 'Invoices, outstanding balances, due dates, and client billing records.', [('invoice_number', 'Invoice #'), ('client', 'Client'), ('status', 'Status'), ('due_date', 'Due'), ('total', 'Total')], ['invoice_number', 'notes']),
    'payments': resource(Payment, 'Payments & Receipts', 'Payment', 'Receipts and payment records linked to invoices and clients.', [('client', 'Client'), ('invoice', 'Invoice'), ('amount', 'Amount'), ('paid_at', 'Paid'), ('method', 'Method')], ['method', 'reference']),
    'expenses': resource(Expense, 'Expenses', 'Expense', 'Operational and project expenses for profitability tracking.', [('title', 'Title'), ('project', 'Project'), ('category', 'Category'), ('amount', 'Amount'), ('spent_at', 'Date')], ['title', 'category', 'notes']),
    'service-packages': resource(ServicePackage, 'Service Packages', 'Package', 'Manage Website Development, SEO, Digital Marketing, Software, Hosting, retainers, features, FAQs, and CTAs.', [('title', 'Package'), ('service_area', 'Service'), ('price', 'Price'), ('billing_cycle', 'Billing'), ('is_active', 'Active')], ['title', 'features', 'faqs']),
    'cms-pages': resource(CMSPage, 'CMS Pages', 'Page', 'Website pages, SEO metadata, body content, and publishing state.', [('title', 'Title'), ('slug', 'Slug'), ('status', 'Status'), ('updated_at', 'Updated')], ['title', 'slug', 'seo_title', 'seo_description', 'body']),
    'website-sections': resource(WebsiteSection, 'Website Sections', 'Section', 'Reusable page sections for navigation, footer, and page content blocks.', [('title', 'Title'), ('page', 'Page'), ('key', 'Key'), ('display_order', 'Order'), ('is_active', 'Active')], ['title', 'key', 'content']),
    'navigation-items': resource(NavigationItem, 'Navigation & Footer', 'Navigation Item', 'Header, footer, and menu links for website navigation.', [('label', 'Label'), ('url', 'URL'), ('location', 'Location'), ('display_order', 'Order'), ('is_active', 'Active')], ['label', 'url', 'location', 'parent_label']),
    'industries': resource(Industry, 'Industries', 'Industry', 'Industry landing-page and targeting content.', [('name', 'Name'), ('slug', 'Slug'), ('is_active', 'Active'), ('updated_at', 'Updated')], ['name', 'slug', 'summary']),
    'markets': resource(Market, 'Markets', 'Market', 'Market, region, or segment landing-page content.', [('name', 'Name'), ('slug', 'Slug'), ('is_active', 'Active'), ('updated_at', 'Updated')], ['name', 'slug', 'summary']),
    'testimonials': resource(Testimonial, 'Testimonials', 'Testimonial', 'Client testimonials and review snippets.', [('name', 'Name'), ('company', 'Company'), ('rating', 'Rating'), ('is_active', 'Active')], ['name', 'company', 'role', 'content']),
    'team-members': resource(TeamMember, 'Team Members', 'Team Member', 'Public team profiles and staff content.', [('name', 'Name'), ('role', 'Role'), ('email', 'Email'), ('display_order', 'Order'), ('is_active', 'Active')], ['name', 'role', 'email', 'bio']),
    'faqs': resource(FAQItem, 'FAQs', 'FAQ', 'Frequently asked questions for service pages, packages, and website content.', [('question', 'Question'), ('category', 'Category'), ('display_order', 'Order'), ('is_active', 'Active')], ['question', 'answer', 'category']),
    'media-assets': resource(MediaAsset, 'Media Library', 'Media Asset', 'Images, documents, and reusable media references.', [('title', 'Title'), ('file_url', 'File URL'), ('alt_text', 'Alt Text'), ('updated_at', 'Updated')], ['title', 'file_url', 'alt_text']),
    'global-settings': resource(GlobalSetting, 'Global Website Settings', 'Setting', 'Global website and system key-value settings.', [('key', 'Key'), ('group', 'Group'), ('updated_at', 'Updated')], ['key', 'value', 'group']),
    'campaigns': resource(Campaign, 'Campaigns', 'Campaign', 'Marketing campaigns, channels, budgets, and attribution notes.', [('name', 'Campaign'), ('channel', 'Channel'), ('status', 'Status'), ('budget', 'Budget'), ('end_date', 'Ends')], ['name', 'channel', 'notes']),
    'seo-settings': resource(SEOSetting, 'SEO Metadata', 'SEO Setting', 'SEO titles, descriptions, noindex controls, and schema JSON.', [('path', 'Path'), ('title', 'Title'), ('noindex', 'Noindex'), ('updated_at', 'Updated')], ['path', 'title', 'description', 'schema_json']),
    'redirects': resource(RedirectRule, 'Redirects', 'Redirect', 'SEO redirects and URL migration rules.', [('from_path', 'From'), ('to_path', 'To'), ('status_code', 'Code'), ('is_active', 'Active')], ['from_path', 'to_path']),
    'career-applications': resource(CareerApplication, 'Career Applications', 'Application', 'Recruitment pipeline and career submissions.', [('name', 'Name'), ('position', 'Position'), ('email', 'Email'), ('status', 'Status'), ('created_at', 'Received')], ['name', 'email', 'phone', 'position', 'message']),
    'employees': resource(Employee, 'Employees', 'Employee', 'Team members, roles, status, and internal assignment references.', [('name', 'Name'), ('email', 'Email'), ('role', 'Role'), ('status', 'Status'), ('start_date', 'Start')], ['name', 'email', 'role', 'notes']),
    'hosting-subscriptions': resource(HostingSubscription, 'Hosting & Subscriptions', 'Subscription', 'Domains, hosting, SSL, maintenance, SEO retainers, marketing retainers, and renewal reminders.', [('client', 'Client'), ('service_type', 'Type'), ('domain', 'Domain'), ('status', 'Status'), ('expiry_date', 'Expiry')], ['service_type', 'domain', 'provider', 'notes']),
    'report-snapshots': resource(ReportSnapshot, 'Reports', 'Report', 'Snapshots for revenue, sales funnel, lead sources, conversions, profitability, and marketing performance.', [('title', 'Title'), ('report_type', 'Type'), ('period_start', 'Start'), ('period_end', 'End'), ('created_at', 'Created')], ['title', 'report_type', 'notes', 'data_json']),
    'audit-logs': resource(AuditLog, 'Audit Logs', 'Audit Log', 'System activity, admin actions, and compliance audit trails.', [('actor', 'Actor'), ('action', 'Action'), ('model_name', 'Model'), ('created_at', 'When')], ['actor', 'action', 'model_name', 'object_repr']),
    'access-roles': resource(AccessRole, 'Roles / RBAC', 'Access Role', 'Role-based access control planning and permission maps.', [('name', 'Name'), ('is_active', 'Active'), ('updated_at', 'Updated')], ['name', 'description', 'permissions']),
    'notification-rules': resource(NotificationRule, 'Notification Rules', 'Notification Rule', 'Email, SMS, WhatsApp and internal alert routing rules.', [('name', 'Name'), ('event', 'Event'), ('channel', 'Channel'), ('is_active', 'Active')], ['name', 'event', 'recipients']),
    'integrations': resource(IntegrationSetting, 'Integrations', 'Integration', 'External service configuration for email, SMS, WhatsApp, analytics, and API connections.', [('name', 'Name'), ('provider', 'Provider'), ('is_active', 'Active'), ('updated_at', 'Updated')], ['name', 'provider', 'config']),
    'api-keys': resource(APIKeyCredential, 'API Keys', 'API Key Reference', 'API key references and provider access notes. Store real secrets outside the dashboard.', [('name', 'Name'), ('provider', 'Provider'), ('key_reference', 'Reference'), ('is_active', 'Active')], ['name', 'provider', 'key_reference', 'notes']),
    'backups': resource(BackupRecord, 'Backups', 'Backup', 'Backup history, scheduled runs, and restore references.', [('label', 'Label'), ('status', 'Status'), ('file_url', 'File'), ('created_at', 'Created')], ['label', 'file_url', 'notes']),
}

CRUD_RESOURCES['access-roles']['form'] = AccessRoleForm
CRUD_RESOURCES['audit-logs']['readonly'] = True
CRUD_RESOURCES['newsletter-deliveries']['readonly'] = True
CRUD_RESOURCES['backups']['readonly'] = True
CRUD_RESOURCES['invoices']['columns'] = [('invoice_number', 'Invoice #'), ('client', 'Client'), ('payment_status', 'Status'), ('due_date', 'Due'), ('total', 'Total'), ('amount_paid', 'Paid'), ('balance', 'Balance')]


def nav_for(request):
    result = []
    for item in DASHBOARD_NAV:
        copy = dict(item)
        if 'children' in item:
            copy['children'] = [dict(child) for child in item['children'] if child.get('url_name') or allowed(request.user, CRUD_RESOURCES[child['resource']]['model'])]
            if not copy['children']:
                continue
            copy['expanded'] = any(child['resource'] in request.path.split('/') for child in copy['children'])
        result.append(copy)
    return result


class AdminLoginView(LoginView):
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True
    template_name = 'dashboard/login.html'
    success_url = reverse_lazy('dashboard')

    def get_success_url(self):
        return str(self.success_url)


@login_required
def dashboard(request):
    today = timezone.localdate()
    today_revenue = Payment.objects.filter(paid_at=today).aggregate(total=Sum('amount'))['total'] or 0
    pipeline_value = Lead.objects.exclude(status__in=[Lead.Status.WON, Lead.Status.LOST]).aggregate(total=Sum('estimated_value'))['total'] or 0
    new_lead_count = Lead.objects.filter(status=Lead.Status.NEW).count()
    overdue_invoices = [invoice for invoice in Invoice.objects.exclude(status__in=['draft', 'cancelled']).filter(due_date__lt=today).prefetch_related('payments') if invoice.balance > 0] if allowed(request.user, Invoice) else []
    active_projects = Project.objects.filter(status=Project.Status.ACTIVE).count()
    pending_tasks = ProjectTask.objects.exclude(status=ProjectTask.Status.DONE).count()
    website_enquiries = Enquiry.objects.filter(status=Enquiry.Status.NEW).count()
    dashboard_stats = [
        {'label': "Today's Revenue", 'value': f'{today_revenue:,.2f}', 'change': 'received today', 'tone': 'success', 'icon': 'ti-cash'},
        {'label': 'Pipeline Value', 'value': f'{pipeline_value:,.2f}', 'change': f'{new_lead_count} new leads', 'tone': 'primary', 'icon': 'ti-target-arrow'},
        {'label': 'Overdue Invoices', 'value': len(overdue_invoices), 'change': f'{sum(invoice.balance for invoice in overdue_invoices):,.2f} due', 'tone': 'danger', 'icon': 'ti-alert-circle'},
        {'label': 'Active Projects', 'value': active_projects, 'change': f'{pending_tasks} pending tasks', 'tone': 'warning', 'icon': 'ti-kanban'},
        {'label': 'Website Enquiries', 'value': website_enquiries, 'change': 'needs review', 'tone': 'info', 'icon': 'ti-inbox'},
        {'label': 'Subscribers', 'value': Subscriber.objects.count(), 'change': f'{Subscriber.objects.filter(status=Subscriber.Status.ACTIVE).count()} active', 'tone': 'azure', 'icon': 'ti-users'},
    ]

    stat_models = [Payment, Lead, Invoice, Project, Enquiry, Subscriber]
    dashboard_stats = [stat for stat, model in zip(dashboard_stats, stat_models) if allowed(request.user, model)]
    recent_requests = Enquiry.objects.order_by('-created_at')[:8] if allowed(request.user, Enquiry) else []
    alerts = []
    if overdue_invoices:
        alerts.append({'tone': 'danger', 'title': 'Overdue invoices', 'message': f'{len(overdue_invoices)} invoices are past due.', 'url': '/dashboard/invoices/?status=overdue'})

    due_followups = FollowUp.objects.filter(status=FollowUp.Status.OPEN, due_at__date__lte=today).count()
    if due_followups and allowed(request.user, FollowUp):
        alerts.append({'tone': 'warning', 'title': 'Follow-ups due', 'message': f'{due_followups} sales follow-ups need attention.', 'url': '/dashboard/follow-ups/?status=open'})

    expiring_subscriptions = HostingSubscription.objects.exclude(status='cancelled').filter(expiry_date__lte=today + timedelta(days=30)).count()
    if expiring_subscriptions and allowed(request.user, HostingSubscription):
        alerts.append({'tone': 'info', 'title': 'Renewals due', 'message': f'{expiring_subscriptions} subscriptions are expired or due within 30 days.', 'url': '/dashboard/hosting-subscriptions/?due=1'})

    if not alerts:
        alerts.append({'tone': 'success', 'title': 'All clear', 'message': 'No urgent alerts right now.'})

    recent_activity = [
        *[{'type': 'Enquiry', 'label': item.name, 'detail': item.get_source_display(), 'created_at': item.created_at} for item in Enquiry.objects.order_by('-created_at')[:4]],
        *[{'type': 'Lead', 'label': item.name, 'detail': item.get_status_display(), 'created_at': item.created_at} for item in Lead.objects.order_by('-created_at')[:4]],
        *[{'type': 'Project', 'label': item.name, 'detail': item.get_status_display(), 'created_at': item.created_at} for item in Project.objects.order_by('-created_at')[:4]],
    ]
    recent_activity = sorted(recent_activity, key=lambda item: item['created_at'], reverse=True)[:10]
    recent_activity = [item for item in recent_activity if allowed(request.user, {'Enquiry': Enquiry, 'Lead': Lead, 'Project': Project}[item['type']])]
    if allowed(request.user, AuditLog):
        recent_activity = [{'type': item.model_name, 'label': item.object_repr, 'detail': f'{item.actor}: {item.action}', 'created_at': item.created_at} for item in AuditLog.objects.all()[:10]]

    return render(
        request,
        'dashboard/index.html',
        {
            'dashboard_stats': dashboard_stats,
            'recent_requests': recent_requests,
            'alerts': alerts,
            'recent_activity': recent_activity,
            'nav_items': nav_for(request),
            'active_resource': 'dashboard',
            'title': 'Command Center',
        },
    )


def _get_resource(resource):
    config = CRUD_RESOURCES.get(resource)
    if not config:
        raise Http404
    return config


def _get_form_class(config):
    if config.get('form'):
        return config['form']
    return modelform_factory(config['model'], form=DashboardModelForm, fields=config.get('fields', '__all__'))


def save_record(request, resource, form):
    try:
        with transaction.atomic():
            if resource == 'payments' and form.cleaned_data.get('invoice'):
                Invoice.objects.select_for_update().get(pk=form.cleaned_data['invoice'].pk)
                form.instance.full_clean()
            if resource == 'quotation-line-items':
                quote = Quotation.objects.select_for_update().get(pk=form.cleaned_data['quotation'].pk)
                if quote.status != 'draft':
                    raise ValidationError('Create a quotation revision before changing issued line items.')
            if resource == 'users' and form.instance.pk == request.user.pk and (not form.cleaned_data['is_staff'] or not form.cleaned_data['is_active']):
                raise ValidationError('Your current account must remain active with staff access.')
            created = not form.instance.pk
            obj = form.save()
            audit(request.user, 'Created' if created else 'Updated', obj)
            return obj
    except ValidationError as error:
        form.add_error(None, '; '.join(error.messages))
        return None


def _apply_search(queryset, fields, query):
    if not query:
        return queryset

    search_filter = Q()
    for field in fields:
        search_filter |= Q(**{f'{field}__icontains': query})
    return queryset.filter(search_filter)


def _display_value(obj, field):
    display_method = getattr(obj, f'get_{field}_display', None)
    if callable(display_method):
        return display_method()

    value = getattr(obj, field)
    if callable(value):
        value = value()
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if value is None or value == '':
        return '-'
    return value


@login_required
def dashboard_list(request, resource):
    config = _get_resource(resource)
    require_permission(request.user, config['model'])
    query = request.GET.get('q', '').strip()
    queryset = _apply_search(config['model'].objects.all().select_related(), config.get('search', []), query)
    status_choices = config['model']._meta.get_field('status').choices if hasattr(config['model'], 'status') else []
    status = request.GET.get('status', '')
    if status and status in dict(status_choices):
        if resource == 'invoices':
            ids = [invoice.pk for invoice in queryset.prefetch_related('payments') if invoice.payment_status == status]
            queryset = queryset.filter(pk__in=ids)
        else:
            queryset = queryset.filter(status=status)
    for relation in ['client', 'project', 'quotation', 'lead']:
        if request.GET.get(relation, '').isdigit() and any(f.name == relation for f in config['model']._meta.fields):
            queryset = queryset.filter(**{f'{relation}_id': request.GET[relation]})
    if resource == 'hosting-subscriptions' and request.GET.get('due'):
        queryset = queryset.exclude(status='cancelled').filter(expiry_date__lte=timezone.localdate() + timedelta(days=30))
    if not queryset.ordered:
        queryset = queryset.order_by('-created_at' if hasattr(config['model'], 'created_at') else 'pk')
    if request.GET.get('export') == 'csv':
        from .workflows import csv_response
        return csv_response(config['title'], [label for _, label in config['columns']], [[_display_value(obj, field) for field, _ in config['columns']] for obj in queryset])
    paginator = Paginator(queryset, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    rows = []
    for obj in page_obj:
        rows.append(
            {
                'object': obj,
                'values': [_display_value(obj, field) for field, _label in config['columns']],
            }
        )

    return render(
        request,
        'dashboard/list.html',
        {
            'config': config,
            'resource': resource,
            'rows': rows,
            'page_obj': page_obj,
            'query': query,
            'status_choices': status_choices,
            'selected_status': status,
            'query_string': request.GET.urlencode(),
            'can_add': allowed(request.user, config['model'], 'add') and not config.get('readonly'),
            'can_change': allowed(request.user, config['model'], 'change') and not config.get('readonly'),
            'can_delete': allowed(request.user, config['model'], 'delete') and not config.get('readonly'),
            'nav_items': nav_for(request),
            'active_resource': resource,
            'title': config['title'],
        },
    )


@login_required
def dashboard_create(request, resource):
    config = _get_resource(resource)
    require_permission(request.user, config['model'], 'add')
    if config.get('readonly'):
        raise PermissionDenied
    form_class = _get_form_class(config)
    initial = {key: value for key, value in request.GET.items() if key in ['client', 'project', 'quotation', 'lead', 'invoice'] and value.isdigit()}
    form = form_class(request.POST if request.method == 'POST' else None, request.FILES or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        obj = save_record(request, resource, form)
        if obj:
            messages.success(request, f'{config["singular"]} created.')
            return redirect('dashboard_detail', resource=resource, pk=obj.pk)

    return render(
        request,
        'dashboard/form.html',
        {
            'config': config,
            'resource': resource,
            'form': form,
            'mode': 'Create',
            'nav_items': nav_for(request),
            'active_resource': resource,
            'title': f'Create {config["singular"]}',
        },
    )


@login_required
def dashboard_edit(request, resource, pk):
    config = _get_resource(resource)
    require_permission(request.user, config['model'], 'change')
    if config.get('readonly'):
        raise PermissionDenied
    obj = get_object_or_404(config['model'], pk=pk)
    form_class = _get_form_class(config)
    form = form_class(request.POST if request.method == 'POST' else None, request.FILES or None, instance=obj)

    if request.method == 'POST' and form.is_valid():
        saved = save_record(request, resource, form)
        if saved:
            messages.success(request, f'{config["singular"]} updated.')
            return redirect('dashboard_detail', resource=resource, pk=obj.pk)

    return render(
        request,
        'dashboard/form.html',
        {
            'config': config,
            'resource': resource,
            'form': form,
            'object': obj,
            'mode': 'Edit',
            'nav_items': nav_for(request),
            'can_delete': allowed(request.user, config['model'], 'delete'),
            'active_resource': resource,
            'title': f'Edit {config["singular"]}',
        },
    )


@login_required
def dashboard_delete(request, resource, pk):
    config = _get_resource(resource)
    require_permission(request.user, config['model'], 'delete')
    if config.get('readonly'):
        raise PermissionDenied
    obj = get_object_or_404(config['model'], pk=pk)

    if request.method == 'POST':
        if resource == 'quotation-line-items' and obj.quotation.status != 'draft':
            messages.error(request, 'Create a quotation revision before deleting issued line items.')
            return redirect('dashboard_detail', resource=resource, pk=obj.pk)
        if resource == 'users' and (obj.pk == request.user.pk or obj.is_superuser):
            messages.error(request, 'Super administrators and your current account cannot be deleted here.')
            return redirect('dashboard_list', resource=resource)
        with transaction.atomic():
            audit(request.user, 'Deleted', obj)
            obj.delete()
        messages.success(request, f'{config["singular"]} deleted.')
        return redirect('dashboard_list', resource=resource)

    return render(
        request,
        'dashboard/confirm_delete.html',
        {
            'config': config,
            'resource': resource,
            'object': obj,
            'nav_items': nav_for(request),
            'active_resource': resource,
            'title': f'Delete {config["singular"]}',
        },
    )


@csrf_exempt
def lead_capture(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Method not allowed.'}, status=405)

    if request.content_type and 'application/json' in request.content_type:
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'ok': False, 'error': 'Invalid JSON.'}, status=400)
        if not isinstance(payload, dict):
            return JsonResponse({'ok': False, 'error': 'Expected a JSON object.'}, status=400)
    else:
        payload = request.POST

    name = str(payload.get('name', '')).strip()
    email = str(payload.get('email', '')).strip()
    message = str(payload.get('message', '')).strip()
    source = str(payload.get('source', Enquiry.Source.CONTACT)).strip() or Enquiry.Source.CONTACT

    if not name or not email or not message:
        return JsonResponse({'ok': False, 'error': 'Name, email, and message are required.'}, status=400)

    enquiry = Enquiry(
        source=source if source in Enquiry.Source.values else Enquiry.Source.CONTACT,
        name=name,
        email=email,
        phone=str(payload.get('phone', '')).strip(),
        subject=str(payload.get('subject', '')).strip(),
        service=str(payload.get('service', '')).strip(),
        message=message,
        utm_source=str(payload.get('utm_source', ''))[:120],
        utm_medium=str(payload.get('utm_medium', ''))[:120],
        utm_campaign=str(payload.get('utm_campaign', ''))[:160],
        landing_page=str(payload.get('landing_page', ''))[:500],
    )
    try:
        enquiry.full_clean()
        enquiry.save()
    except ValidationError as error:
        return JsonResponse({'ok': False, 'error': '; '.join(error.messages)}, status=400)

    return JsonResponse({'ok': True, 'id': enquiry.pk})


@login_required
@require_POST
@transaction.atomic
def convert_enquiry(request, pk):
    require_permission(request.user, Enquiry, 'change')
    require_permission(request.user, Lead, 'add')
    enquiry = get_object_or_404(Enquiry.objects.select_for_update(), pk=pk)

    if enquiry.converted_lead_id:
        messages.info(request, 'This enquiry is already connected to a CRM lead.')
        return redirect('dashboard_edit', resource='leads', pk=enquiry.converted_lead_id)

    lead = Lead.objects.filter(email__iexact=enquiry.email).exclude(status__in=['won', 'lost']).first()
    if not lead:
        lead = Lead.objects.create(
        source=Lead.Source.QUOTE if enquiry.source == Enquiry.Source.QUOTE else Lead.Source.CONTACT,
        name=enquiry.name,
        email=enquiry.email,
        phone=enquiry.phone,
        subject=enquiry.subject,
        service=enquiry.service,
        message=enquiry.message,
        internal_notes=enquiry.internal_notes,
        )
    enquiry.converted_lead = lead
    enquiry.status = Enquiry.Status.CONVERTED
    enquiry.save(update_fields=['converted_lead', 'status', 'updated_at'])
    audit(request.user, 'Converted to CRM lead', enquiry, lead_id=lead.pk)
    messages.success(request, 'Enquiry converted into a CRM lead.')
    return redirect('dashboard_edit', resource='leads', pk=lead.pk)


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


PAGE_ALIASES = {
    '': 'index.html',
    'index.html': 'index.html',
    'about.html': 'about us.html',
    'about-us.html': 'about us.html',
    'career-details.html': 'careers single.html',
    'careers-single.html': 'careers single.html',
    'coming-soon.html': 'coming soon.html',
    'contact.html': 'contact us.html',
    'contact-us.html': 'contact us.html',
    'insight-single.html': 'insight single.html',
    'portfolio-single.html': 'portfolio single.html',
    'privacy-policy.html': 'privacy policy.html',
    'service-single.html': 'service single.html',
    'team-single.html': 'team single.html',
    'terms-and-conditions.html': 'terms and conditions.html',
}

PAGES = {
    '404.html',
    'about us.html',
    'careers single.html',
    'careers.html',
    'coming soon.html',
    'contact us.html',
    'faq.html',
    'index.html',
    'insight single.html',
    'insights.html',
    'portfolio single.html',
    'portfolio.html',
    'pricing.html',
    'privacy policy.html',
    'service single.html',
    'services.html',
    'team single.html',
    'team.html',
    'terms and conditions.html',
}


def home(request):
    return page(request, '')


def page(request, page_path):
    template_name = PAGE_ALIASES.get(page_path, page_path)
    if template_name == 'portfolio.html':
        from .public import portfolio_redirect
        return portfolio_redirect(request)
    if template_name == 'insights.html':
        from .public import content
        if Insight.objects.filter(status='published').exists():
            return content(request, 'insights')

    if template_name not in PAGES:
        return render(request, 'site/404.html', status=404)

    return render(request, f'site/{template_name}')


def partial(request, partial_path):
    allowed_partials = {
        'footer.html',
        'header.html',
        'preloader.html',
        'site-widgets.html',
    }

    if partial_path not in allowed_partials:
        raise Http404

    return render(request, f'partials/{partial_path}')

# Create your views here.
