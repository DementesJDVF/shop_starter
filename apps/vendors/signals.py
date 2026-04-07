"""Signals for vendor profile lifecycle."""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.constants import UserRoles
from apps.users.models import User
from apps.vendors.models import VendorProfile


@receiver(post_save, sender=User)
def ensure_vendor_profile_for_vendor_role(sender, instance: User, **kwargs):
    """Create VendorProfile automatically for users with VENDOR role.

    This keeps ``VendorProfile`` as an extension object while role ownership lives
    in ``User.role``.
    """
    if instance.role == UserRoles.VENDOR:
        VendorProfile.objects.get_or_create(user=instance)