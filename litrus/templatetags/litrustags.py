from hashlib import md5

from django import template
import markdown2


register = template.Library()

@register.filter
def markdownify(value):
    return markdown2.markdown(value, extras=['fenced-code-blocks'])

@register.simple_tag
def gravatar(email):
    """
    Generate gravatar image url.
    https://en.gravatar.com/site/implement/images/python/
    """
    email_hash = md5(email.strip().lower()).hexdigest()
    url = 'http://www.gravatar.com/avatar/{0}?d=identicon'.format(email_hash)
    return url
