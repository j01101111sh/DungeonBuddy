import markdown as md
import nh3
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
@stringfilter
def markdown_format(value: str) -> str:
    """
    Convert a markdown string to HTML and sanitize it.

    Args:
        value (str): The markdown text to convert.

    Returns:
        str: The converted and sanitized HTML string, marked as safe.
    """
    # 1. Convert Markdown to HTML
    html_content = md.markdown(
        value,
        extensions=[
            "markdown.extensions.fenced_code",
            "markdown.extensions.tables",
        ],
    )

    # 2. Define allowed tags (Defaults + Tables + Code blocks)
    # nh3.ALLOWED_TAGS includes: a, b, blockquote, br, code, dd, div, dl, dt, em,
    # h1-h6, hr, i, img, li, ol, p, pre, strong, ul, etc.
    # We ensure table-related tags are explicitly included.
    allowed_tags = nh3.ALLOWED_TAGS | {
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "th",
        "td",
        "span",
    }

    # 3. Sanitize the HTML
    # This strips out any tags (like <script>) not in the allowed list.
    clean_content = nh3.clean(html_content, tags=allowed_tags)

    # 4. Mark as safe
    # We can safely mark this as safe because we have just sanitized it.
    # The '# nosec B308' comment suppresses the Bandit security warning.
    return mark_safe(clean_content)  # nosec
