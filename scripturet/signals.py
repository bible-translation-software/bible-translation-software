from allauth.account.signals import user_signed_up
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import mail_managers
from .models import UserProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        up = UserProfile(user=instance)
        up.full_clean()
        up.save()

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.full_clean()
    instance.userprofile.save()


@receiver(user_signed_up)
def callback_user_signed_up(request, user, **kwargs):
    mail_managers(
        subject="A new user signed up",
        message="A new user has signed up.\n\nUsername: %s\nEmail address: %s" % (user.username, user.email),
        fail_silently=True,
    )


