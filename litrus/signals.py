from base64 import b16decode
from datetime import timedelta

from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received


@receiver(valid_ipn_received)
def paypal_ipn_receiver(sender, **kwargs):
    # Lazy imports here.
    from litrus.models import Subscription, SubscriptionPlan

    if sender.payment_status == ST_PP_COMPLETED:
        email = b16decode(sender.custom)
        user = User.objects.get(email=email)
        plan = SubscriptionPlan.objects.get(id=sender.item_number)
        days_to_add = timedelta(days=plan.months*31)
        try:
            sub = Subscription.objects.get(user=user)
            sub.date_expiration += days_to_add
        except Subscription.DoesNotExist:
            date_expiration = timezone.now() + days_to_add
            sub = Subscription(user=user, date_expiration=date_expiration)
        sub.save()
