from django.urls import include, path

from . import views, workflows, operations, public


urlpatterns = [
    path('newsletter/subscribe/', public.subscribe, name='subscribe'),
    path('newsletter/unsubscribe/<str:token>/', public.unsubscribe, name='unsubscribe'),
    path('careers/apply/', public.apply_for_job, name='apply_for_job'),
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
    path('case-studies/', include('case_studies.urls')),
    path('portfolio/', public.portfolio_redirect, name='portfolio_redirect'),
    path('portfolio/<slug:slug>/', public.portfolio_redirect, name='portfolio_detail_redirect'),
    path('insights/', public.content, {'kind': 'insights'}, name='published_insights'),
    path('insights/<slug:slug>/', public.content, {'kind': 'insights'}, name='published_insight'),
    path('pages/<slug:slug>/', public.content, {'kind': 'pages'}, name='published_page'),
    path('services/<slug:slug>/', public.content, {'kind': 'services'}, name='published_service'),
    path('industries/<slug:slug>/', public.content, {'kind': 'industries'}, name='published_industry'),
    path('markets/<slug:slug>/', public.content, {'kind': 'markets'}, name='published_market'),
    path('<path:page_path>', views.page, name='page'),
]
