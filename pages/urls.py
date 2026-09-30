from django.urls import include, path

from . import views, workflows, operations, public


urlpatterns = [
    path('newsletter/subscribe/', public.subscribe, name='subscribe'),
    path('newsletter/unsubscribe/<str:token>/', public.unsubscribe, name='unsubscribe'),
    path('sitemap.xml', public.sitemap, name='sitemap'),
    path('api/leads/', views.lead_capture, name='lead_capture'),
    path('login/', views.AdminLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/backups/create/', operations.create_backup, name='dashboard_backup'),
    path('dashboard/reports/', workflows.reports, name='dashboard_reports'),
    path('dashboard/files/<path:path>', workflows.download_file, name='dashboard_file'),
    path('dashboard/<slug:resource>/board/', workflows.board, name='dashboard_board'),
    path('dashboard/<slug:resource>/<int:pk>/', workflows.detail, name='dashboard_detail'),
    path('dashboard/<slug:resource>/<int:pk>/action/<slug:operation>/', workflows.action, name='dashboard_action'),
    path('dashboard/<slug:resource>/<int:pk>/move/', workflows.move_card, name='dashboard_move'),
    path('dashboard/<slug:resource>/<int:pk>/document/', workflows.document, name='dashboard_document'),
    path('dashboard/<slug:resource>/', views.dashboard_list, name='dashboard_list'),
    path('dashboard/<slug:resource>/new/', views.dashboard_create, name='dashboard_create'),
    path('dashboard/enquiries/<int:pk>/convert/', views.convert_enquiry, name='convert_enquiry'),
    path('dashboard/<slug:resource>/<int:pk>/edit/', views.dashboard_edit, name='dashboard_edit'),
    path('dashboard/<slug:resource>/<int:pk>/delete/', views.dashboard_delete, name='dashboard_delete'),
    path('', views.home, name='home'),

    # Clean public website URLs
    path('about/', views.page, {'page_path': 'about us.html'}, name='about'),
    path('careers/', views.page, {'page_path': 'careers.html'}, name='careers'),
    path('contact/', views.page, {'page_path': 'contact us.html'}, name='contact'),
    path('faq/', views.page, {'page_path': 'faq.html'}, name='faq'),
    path('pricing/', views.page, {'page_path': 'pricing.html'}, name='pricing'),
    path('services/', views.page, {'page_path': 'services.html'}, name='services'),
    path('team/<int:member_id>/', views.team_member_detail, name='team_member'),
    path('team/', views.page, {'page_path': 'team.html'}, name='team'),
    path('privacy-policy/', views.page, {'page_path': 'privacy policy.html'}, name='privacy_policy'),
    path('terms-and-conditions/', views.page, {'page_path': 'terms and conditions.html'}, name='terms'),
    path('coming-soon/', views.page, {'page_path': 'coming soon.html'}, name='coming_soon'),

    path('case-studies/', include('case_studies.urls')),
    path('portfolio/', public.portfolio_redirect, name='portfolio_redirect'),
    path('portfolio/<slug:slug>/', public.portfolio_redirect, name='portfolio_detail_redirect'),
    path('insights/', public.content, {'kind': 'insights'}, name='published_insights'),
    path('insights/<slug:slug>/', public.content, {'kind': 'insights'}, name='published_insight'),
    path('services/<slug:slug>/', public.service_page, name='service_page'),
    path('industries/<slug:slug>/', public.content, {'kind': 'industries'}, name='published_industry'),
    path('markets/<slug:slug>/', public.content, {'kind': 'markets'}, name='published_market'),
    path('<path:page_path>', views.page, name='page'),
]
