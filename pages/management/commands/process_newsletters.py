from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMessage
from django.core import signing
from django.db import transaction
from django.utils import timezone
from pages.models import Newsletter, NewsletterDelivery, Subscriber


class Command(BaseCommand):
    help = 'Deliver due scheduled newsletters using the configured email backend.'

    def handle(self, *args, **options):
        backend = settings.MAILERS['default']['BACKEND']
        if backend.endswith(('console.EmailBackend', 'locmem.EmailBackend', 'dummy.EmailBackend')):
            raise CommandError('Configure a real email backend before delivering newsletters.')
        count = 0
        for pk in Newsletter.objects.filter(status='scheduled', scheduled_at__lte=timezone.now()).values_list('pk', flat=True):
            with transaction.atomic():
                newsletter = Newsletter.objects.select_for_update(skip_locked=True).filter(pk=pk, status='scheduled').first()
                if not newsletter:
                    continue
                for subscriber in Subscriber.objects.filter(status='active'):
                    delivery, _ = NewsletterDelivery.objects.get_or_create(newsletter=newsletter, subscriber=subscriber)
                    if delivery.status == 'sent':
                        continue
                    token = signing.dumps(subscriber.pk, salt='newsletter-unsubscribe')
                    link = f'{settings.PUBLIC_SITE_URL}/newsletter/unsubscribe/{token}/'
                    body = f'{newsletter.content}\n\nUnsubscribe: {link}'
                    try:
                        sent = EmailMessage(newsletter.subject, body, settings.DEFAULT_FROM_EMAIL, [subscriber.email]).send()
                        if not sent:
                            raise RuntimeError('Email backend did not accept the message.')
                        delivery.status, delivery.sent_at, delivery.error = 'sent', timezone.now(), ''
                        count += 1
                    except Exception as error:
                        delivery.status = 'failed'
                        delivery.error = type(error).__name__
                    delivery.save()
                if not newsletter.deliveries.exclude(status='sent').exists():
                    newsletter.status, newsletter.sent_at = 'sent', timezone.now()
                    newsletter.save()
        self.stdout.write(f'{count} messages delivered.')
