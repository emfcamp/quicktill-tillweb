"""
"markdown" template filter for Django.

Copied from django.contrib.markup which is now deprecated for security
reasons.  Markdown is only being provided by trusted users in the
ipladmin application, so we don't worry about using it.

"""

from django import template
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
import markdown as markdown_module

markdown_extensions = [
    "markup.mdx_plimg:PLImgExtension",
    "def_list",
]


register = template.Library()


@register.filter(is_safe=True)
def markdown(value, arg=''):
    """
    Runs Markdown over a given value, optionally using various
    extensions python-markdown supports.

    Syntax::

        {{ value|markdown }}

    """
    return mark_safe(
        markdown_module.markdown(
            force_str(value),
            extensions=markdown_extensions))


@register.tag(name="markdown")
def markdown_tag(parser, token):
    nodelist = parser.parse(('endmarkdown',))
    bits = token.split_contents()
    if len(bits) != 1:
        raise template.TemplateSyntaxError(
            "`markdown` tag requires exactly zero arguments")
    parser.delete_first_token()
    return MarkdownNode(nodelist)


class MarkdownNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        doc = self.nodelist.render(context)
        return mark_safe(markdown_module.markdown(
            doc, extensions=markdown_extensions))
