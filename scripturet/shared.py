from django.utils.functional import keep_lazy_text
from django.utils.html import normalize_newlines, escape
from django.utils.safestring import mark_safe
import re

@keep_lazy_text
def auto_paragraphs(text):
    """Given a string, return that string escaped for HTML, broken into
    paragraphs, with the dir HTML attribute set to "auto".

    The reason why it is important to set dir="auto" on every paragraph is
    because that matches the behaviour of <textarea dir="auto">.

    For example:

    >>> auto_paragraphs("Tom & Jerry\nBugs Bunny")
    '<p dir="auto">Tom &amp; Jerry</p>\n\n<p dir="auto">Bugs Bunny</p>'
    """

    text = normalize_newlines(text)
    parts = re.split('\\s*\n\\s*', str(text))
    parts = ['<p dir="auto">%s</p>' % (escape(p),) for p in parts]
    return mark_safe('\n\n'.join(parts))
