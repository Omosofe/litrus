from hashlib import md5
from uuid import uuid4

from litrus.models import *


def is_user_subscribed(user):
    try:
        sub = Subscription.objects.get(user=user)
        if not sub.has_expired():
            return True
    except Subscription.DoesNotExist:
        pass
    
    return False

def is_user_enrolled(user, course):
    try:
        CourseEnrollment.objects.get(user=user, course=course)
        return True
    except CourseEnrollment.DoesNotExist:
        return False

def random_hash():
    return md5(str(uuid4())).hexdigest()
