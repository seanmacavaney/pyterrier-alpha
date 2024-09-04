"""This module provides utilities for working with Google Colab."""
import colaburl
from deprecated import deprecated

_REASON = 'Use the colaburl package instead. pyterrier_alpha.colab will be removed in a future version.'
_VERSION = '0.9.0'

code_url = deprecated(version=_VERSION, reason=_REASON)(colaburl.code_url)
code_html_link = deprecated(version=_VERSION, reason=_REASON)(colaburl.code_html_link)
code_html_form = deprecated(version=_VERSION, reason=_REASON)(colaburl.code_html_form)
code_html = deprecated(version=_VERSION, reason=_REASON)(colaburl.code_html)
