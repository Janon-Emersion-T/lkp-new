from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Quotation, QuotationLineItem, FollowUp
from django.utils import timezone


@receiver(pre_save, sender=QuotationLineItem)
def remember_quotation(sender, instance, **kwargs):
    instance._previous_quote = sender.objects.filter(pk=instance.pk).values_list('quotation_id', flat=True).first()


@receiver(post_save, sender=QuotationLineItem)
@receiver(post_delete, sender=QuotationLineItem)
def calculate_quote(sender, instance, **kwargs):
    for quote in Quotation.objects.filter(pk__in=[instance.quotation_id, getattr(instance, '_previous_quote', None)]):
        quote.recalculate()


@receiver(post_save, sender=Quotation)
def calculate_quote_adjustments(sender, instance, **kwargs):
    instance.recalculate()


@receiver(pre_save, sender=FollowUp)
def complete_follow_up(sender, instance, **kwargs):
    instance.completed_at = (instance.completed_at or timezone.now()) if instance.status == 'done' else None
