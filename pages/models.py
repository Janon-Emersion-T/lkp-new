from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def clean(self):
        from .validation import validate_record
        super().clean()
        validate_record(self)


class SluggedModel(TimeStampedModel):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(SluggedModel):
    class Meta(SluggedModel.Meta):
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'


class Category(SluggedModel):
    description = models.TextField(blank=True)

    class Meta(SluggedModel.Meta):
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class ServiceArea(SluggedModel):
    summary = models.TextField(blank=True)
    icon = models.CharField(max_length=80, blank=True, help_text='Tabler or Font Awesome icon class')
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']


class Insight(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='insights')
    tags = models.ManyToManyField(Tag, blank=True, related_name='insights')
    summary = models.TextField(blank=True)
    content = models.TextField(blank=True)
    image_url = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Subscriber(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        UNSUBSCRIBED = 'unsubscribed', 'Unsubscribed'
        BOUNCED = 'bounced', 'Bounced'

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=160, blank=True)
    source = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class PipelineStage(SluggedModel):
    probability = models.PositiveIntegerField(default=10)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']


class LeadSource(SluggedModel):
    description = models.TextField(blank=True)
    utm_source = models.CharField(max_length=120, blank=True)


class Company(TimeStampedModel):
    class Status(models.TextChoices):
        PROSPECT = 'prospect', 'Prospect'
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'

    name = models.CharField(max_length=220)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=80, blank=True)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROSPECT)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name


class Contact(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contacts', null=True, blank=True)
    name = models.CharField(max_length=180)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=80, blank=True)
    job_title = models.CharField(max_length=160, blank=True)
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Client(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ON_HOLD = 'on_hold', 'On Hold'
        INACTIVE = 'inactive', 'Inactive'

    company = models.OneToOneField(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='client_profile')
    name = models.CharField(max_length=220)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=80, blank=True)
    website = models.URLField(blank=True)
    billing_address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    account_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ClientCommunication(TimeStampedModel):
    class Type(models.TextChoices):
        EMAIL = 'email', 'Email'
        CALL = 'call', 'Call'
        MEETING = 'meeting', 'Meeting'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        NOTE = 'note', 'Note'

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='communications')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='communications')
    communication_type = models.CharField(max_length=20, choices=Type.choices, default=Type.NOTE)
    subject = models.CharField(max_length=220, blank=True)
    notes = models.TextField()
    happened_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-happened_at']

    def __str__(self):
        return self.subject or f'{self.client} communication'


class ClientFile(TimeStampedModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='files')
    title = models.CharField(max_length=220)
    file_url = models.CharField(max_length=500)
    category = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.title


class ClientCredential(TimeStampedModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='credentials')
    label = models.CharField(max_length=220)
    reference = models.CharField(max_length=260, blank=True)
    secret_hint = models.CharField(max_length=260, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.label


class Enquiry(TimeStampedModel):
    class Source(models.TextChoices):
        CONTACT = 'contact', 'Contact Form'
        QUOTE = 'quote', 'Get Quote'
        CONSULTATION = 'consultation', 'Consultation Request'
        CAREER = 'career', 'Career/Application'
        NEWSLETTER = 'newsletter', 'Newsletter'

    class Status(models.TextChoices):
        NEW = 'new', 'New'
        REVIEWING = 'reviewing', 'Reviewing'
        CONVERTED = 'converted', 'Converted'
        CLOSED = 'closed', 'Closed'

    source = models.CharField(max_length=24, choices=Source.choices, default=Source.CONTACT)
    name = models.CharField(max_length=180)
    email = models.EmailField()
    phone = models.CharField(max_length=80, blank=True)
    subject = models.CharField(max_length=220, blank=True)
    service = models.CharField(max_length=180, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    converted_lead = models.ForeignKey('Lead', on_delete=models.SET_NULL, null=True, blank=True, related_name='source_enquiries')
    internal_notes = models.TextField(blank=True)
    utm_source = models.CharField(max_length=120, blank=True)
    utm_medium = models.CharField(max_length=120, blank=True)
    utm_campaign = models.CharField(max_length=160, blank=True)
    landing_page = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Enquiries'

    def __str__(self):
        return f'{self.name} - {self.get_source_display()}'


class Portfolio(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    client_name = models.CharField(max_length=180, blank=True)
    service_area = models.ForeignKey(ServiceArea, on_delete=models.SET_NULL, null=True, blank=True, related_name='portfolios')
    industry = models.ForeignKey('Industry', on_delete=models.SET_NULL, null=True, blank=True, related_name='portfolios')
    summary = models.TextField(blank=True)
    content = models.TextField(blank=True)
    challenge = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    results = models.TextField(blank=True)
    key_features = models.TextField(blank=True, help_text='One feature per line')
    technology_stack = models.TextField(blank=True, help_text='One technology or capability per line')
    key_result = models.CharField(max_length=260, blank=True)
    image_url = models.CharField(max_length=500, blank=True)
    gallery_urls = models.TextField(blank=True, help_text='One image URL per line')
    project_url = models.URLField(blank=True)
    seo_title = models.CharField(max_length=260, blank=True)
    seo_description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_featured = models.BooleanField(default=False)
    completed_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-completed_at', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Newsletter(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SCHEDULED = 'scheduled', 'Scheduled'
        SENT = 'sent', 'Sent'
        ARCHIVED = 'archived', 'Archived'

    subject = models.CharField(max_length=220)
    preheader = models.CharField(max_length=220, blank=True)
    content = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.subject


class Lead(TimeStampedModel):
    class Source(models.TextChoices):
        QUOTE = 'quote', 'Get Quote'
        CONTACT = 'contact', 'Contact Form'
        MANUAL = 'manual', 'Manual'

    class Status(models.TextChoices):
        NEW = 'new', 'New'
        CONTACTED = 'contacted', 'Contacted'
        QUALIFIED = 'qualified', 'Qualified'
        WON = 'won', 'Won'
        LOST = 'lost', 'Lost'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    pipeline_stage = models.ForeignKey(PipelineStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    lead_source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    name = models.CharField(max_length=180)
    email = models.EmailField()
    phone = models.CharField(max_length=80, blank=True)
    subject = models.CharField(max_length=220, blank=True)
    service = models.CharField(max_length=180, blank=True)
    message = models.TextField()
    score = models.PositiveIntegerField(default=0)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    next_follow_up = models.DateTimeField(null=True, blank=True)
    lost_reason = models.CharField(max_length=220, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    internal_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.get_source_display()}'


class FollowUp(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        DONE = 'done', 'Done'
        MISSED = 'missed', 'Missed'

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='follow_ups')
    due_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['due_at']

    def __str__(self):
        return f'{self.lead} follow-up'


class ServicePackage(TimeStampedModel):
    class BillingCycle(models.TextChoices):
        ONE_TIME = 'one_time', 'One Time'
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'

    service_area = models.ForeignKey(ServiceArea, on_delete=models.SET_NULL, null=True, blank=True, related_name='packages')
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    billing_cycle = models.CharField(max_length=20, choices=BillingCycle.choices, default=BillingCycle.ONE_TIME)
    features = models.TextField(blank=True)
    faqs = models.TextField(blank=True)
    cta_label = models.CharField(max_length=120, default='Get Started')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['service_area', 'price', 'title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Quotation(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SENT = 'sent', 'Sent'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        EXPIRED = 'expired', 'Expired'

    quote_number = models.CharField(max_length=40, unique=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    title = models.CharField(max_length=220)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    revision = models.PositiveIntegerField(default=1)
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    revised_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='revisions')

    def recalculate(self):
        self.subtotal = sum((item.total for item in self.line_items.all()), Decimal('0'))
        self.total = max(self.subtotal - self.discount + self.tax, Decimal('0'))
        type(self).objects.filter(pk=self.pk).update(subtotal=self.subtotal, total=self.total)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.quote_number


class QuotationLineItem(TimeStampedModel):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=260)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    package = models.ForeignKey(ServicePackage, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.total = (self.quantity * self.unit_price).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.description


class Project(TimeStampedModel):
    class Status(models.TextChoices):
        PLANNING = 'planning', 'Planning'
        ACTIVE = 'active', 'Active'
        ON_HOLD = 'on_hold', 'On Hold'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    quotation = models.ForeignKey(Quotation, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    name = models.CharField(max_length=220)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNING)
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profitability_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    requirements = models.TextField(blank=True)
    deployment_info = models.TextField(blank=True)
    team = models.ManyToManyField('Employee', blank=True, related_name='projects')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ProjectMilestone(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=220)
    due_date = models.DateField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['due_date', 'title']

    def __str__(self):
        return self.title


class ProjectTask(TimeStampedModel):
    class Status(models.TextChoices):
        TODO = 'todo', 'To Do'
        DOING = 'doing', 'Doing'
        REVIEW = 'review', 'Review'
        DONE = 'done', 'Done'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    milestone = models.ForeignKey(ProjectMilestone, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    title = models.CharField(max_length=220)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    assigned_to = models.CharField(max_length=180, blank=True)
    employee = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['due_date', 'title']

    def __str__(self):
        return self.title


class ProjectFile(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    title = models.CharField(max_length=220)
    file_url = models.CharField(max_length=500)
    category = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Invoice(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SENT = 'sent', 'Sent'
        PAID = 'paid', 'Paid'
        OVERDUE = 'overdue', 'Overdue'
        CANCELLED = 'cancelled', 'Cancelled'

    invoice_number = models.CharField(max_length=40, unique=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    quotation = models.ForeignKey(Quotation, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    subscription = models.ForeignKey('HostingSubscription', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    billing_period = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['subscription', 'billing_period'], name='unique_subscription_billing_period')]

    def __str__(self):
        return self.invoice_number

    @property
    def amount_paid(self):
        return sum((payment.amount for payment in self.payments.all()), Decimal('0'))

    @property
    def balance(self):
        return max(self.total - self.amount_paid, Decimal('0'))

    @property
    def payment_status(self):
        if self.status == self.Status.CANCELLED:
            return self.Status.CANCELLED
        if self.total > 0 and self.balance == 0:
            return self.Status.PAID
        if self.status != self.Status.DRAFT and self.due_date and self.due_date < timezone.localdate():
            return self.Status.OVERDUE
        return self.Status.SENT if self.status == self.Status.PAID else self.status


class Payment(TimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_at = models.DateField(default=timezone.localdate)
    method = models.CharField(max_length=80, blank=True)
    reference = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f'{self.amount} payment'


class Expense(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    title = models.CharField(max_length=220)
    category = models.CharField(max_length=120, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    spent_at = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-spent_at']

    def __str__(self):
        return self.title


class CMSPage(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    seo_title = models.CharField(max_length=220, blank=True)
    seo_description = models.TextField(blank=True)
    body = models.TextField(blank=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class WebsiteSection(TimeStampedModel):
    page = models.ForeignKey(CMSPage, on_delete=models.CASCADE, related_name='sections', null=True, blank=True)
    title = models.CharField(max_length=220)
    key = models.CharField(max_length=120, blank=True)
    content = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'title']

    def __str__(self):
        return self.title


class NavigationItem(TimeStampedModel):
    label = models.CharField(max_length=160)
    url = models.CharField(max_length=260)
    location = models.CharField(max_length=80, default='header')
    parent_label = models.CharField(max_length=160, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['location', 'display_order', 'label']

    def __str__(self):
        return self.label


class Industry(TimeStampedModel):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    summary = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Industries'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Market(TimeStampedModel):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    summary = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class TeamMember(TimeStampedModel):
    name = models.CharField(max_length=180)
    role = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    bio = models.TextField(blank=True)
    image_url = models.CharField(max_length=500, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class Testimonial(TimeStampedModel):
    name = models.CharField(max_length=180)
    company = models.CharField(max_length=180, blank=True)
    role = models.CharField(max_length=120, blank=True)
    content = models.TextField()
    rating = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class FAQItem(TimeStampedModel):
    question = models.CharField(max_length=260)
    answer = models.TextField()
    category = models.CharField(max_length=120, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'question']

    def __str__(self):
        return self.question


class MediaAsset(TimeStampedModel):
    title = models.CharField(max_length=220)
    file_url = models.CharField(max_length=500)
    alt_text = models.CharField(max_length=220, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.title


class GlobalSetting(TimeStampedModel):
    key = models.CharField(max_length=160, unique=True)
    value = models.TextField(blank=True)
    group = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ['group', 'key']

    def __str__(self):
        return self.key


class Campaign(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        COMPLETE = 'complete', 'Complete'

    name = models.CharField(max_length=220)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    channel = models.CharField(max_length=120, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class RedirectRule(TimeStampedModel):
    from_path = models.CharField(max_length=260, unique=True)
    to_path = models.CharField(max_length=260)
    status_code = models.PositiveIntegerField(default=301)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.from_path} -> {self.to_path}'


class SEOSetting(TimeStampedModel):
    path = models.CharField(max_length=260, unique=True)
    title = models.CharField(max_length=220, blank=True)
    description = models.TextField(blank=True)
    schema_json = models.TextField(blank=True)
    noindex = models.BooleanField(default=False)

    def __str__(self):
        return self.path


class CareerApplication(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        SCREENING = 'screening', 'Screening'
        INTERVIEW = 'interview', 'Interview'
        OFFER = 'offer', 'Offer'
        REJECTED = 'rejected', 'Rejected'

    name = models.CharField(max_length=180)
    email = models.EmailField()
    phone = models.CharField(max_length=80, blank=True)
    position = models.CharField(max_length=180)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    resume_url = models.CharField(max_length=500, blank=True)
    message = models.TextField(blank=True)

    def __str__(self):
        return f'{self.name} - {self.position}'


class Employee(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ON_LEAVE = 'on_leave', 'On Leave'
        INACTIVE = 'inactive', 'Inactive'

    name = models.CharField(max_length=180)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    start_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class HostingSubscription(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRING = 'expiring', 'Expiring'
        EXPIRED = 'expired', 'Expired'
        CANCELLED = 'cancelled', 'Cancelled'

    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='subscriptions')
    service_type = models.CharField(max_length=120)
    domain = models.CharField(max_length=220, blank=True)
    provider = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    start_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    renewal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['expiry_date', 'domain']

    def __str__(self):
        return self.domain or self.service_type


class ReportSnapshot(TimeStampedModel):
    report_type = models.CharField(max_length=160)
    title = models.CharField(max_length=220)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    data_json = models.TextField(blank=True)

    def __str__(self):
        return self.title


class AuditLog(TimeStampedModel):
    actor = models.CharField(max_length=180, blank=True)
    action = models.CharField(max_length=220)
    model_name = models.CharField(max_length=160, blank=True)
    object_repr = models.CharField(max_length=260, blank=True)
    metadata = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.action


class AccessRole(TimeStampedModel):
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    permissions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='dashboard_roles')

    def __str__(self):
        return self.name


class NotificationRule(TimeStampedModel):
    name = models.CharField(max_length=180)
    event = models.CharField(max_length=160)
    channel = models.CharField(max_length=80, default='email')
    recipients = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class IntegrationSetting(TimeStampedModel):
    name = models.CharField(max_length=180)
    provider = models.CharField(max_length=120)
    is_active = models.BooleanField(default=False)
    config = models.TextField(blank=True)

    def __str__(self):
        return self.name


class APIKeyCredential(TimeStampedModel):
    name = models.CharField(max_length=180)
    provider = models.CharField(max_length=120, blank=True)
    key_reference = models.CharField(max_length=260, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class BackupRecord(TimeStampedModel):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETE = 'complete', 'Complete'
        FAILED = 'failed', 'Failed'

    label = models.CharField(max_length=180)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    file_url = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.label


class SupportTicket(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='support_tickets')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=220)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    resolution = models.TextField(blank=True)

    def __str__(self):
        return self.subject


class NewsletterDelivery(TimeStampedModel):
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE, related_name='deliveries')
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], default='pending')
    error = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['newsletter', 'subscriber'], name='unique_newsletter_recipient')]

    def __str__(self):
        return f'{self.newsletter} / {self.subscriber}'
