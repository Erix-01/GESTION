
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AuditLog, Client, Vehicule, Contrat
from django.forms.models import model_to_dict
from django.conf import settings

def actor_from_sender(sender, instance):
    # placeholder; we can't reliably get request.user here without middleware.
    return getattr(instance, '_last_actor', '')

@receiver(post_save, sender=Client)
def audit_client_save(sender, instance, created, **kwargs):
    AuditLog.objects.create(
        actor=actor_from_sender(sender, instance),
        model=sender.__name__,
        object_id=str(instance.id),
        action='created' if created else 'updated',
        changes=str(model_to_dict(instance))
    )

@receiver(post_delete, sender=Client)
def audit_client_delete(sender, instance, **kwargs):
    AuditLog.objects.create(
        actor=actor_from_sender(sender, instance),
        model=sender.__name__,
        object_id=str(instance.id),
        action='deleted',
        changes=''
    )

# same for Vehicule and Contrat
@receiver(post_save, sender=Vehicule)
def audit_vehicule_save(sender, instance, created, **kwargs):
    AuditLog.objects.create(actor=actor_from_sender(sender, instance), model=sender.__name__, object_id=str(instance.id), action='created' if created else 'updated', changes=str(model_to_dict(instance)))

@receiver(post_delete, sender=Vehicule)
def audit_vehicule_delete(sender, instance, **kwargs):
    AuditLog.objects.create(actor=actor_from_sender(sender, instance), model=sender.__name__, object_id=str(instance.id), action='deleted', changes='')

@receiver(post_save, sender=Contrat)
def audit_contrat_save(sender, instance, created, **kwargs):
    AuditLog.objects.create(actor=actor_from_sender(sender, instance), model=sender.__name__, object_id=str(instance.id), action='created' if created else 'updated', changes=str(model_to_dict(instance)))

@receiver(post_delete, sender=Contrat)
def audit_contrat_delete(sender, instance, **kwargs):
    AuditLog.objects.create(actor=actor_from_sender(sender, instance), model=sender.__name__, object_id=str(instance.id), action='deleted', changes='')
