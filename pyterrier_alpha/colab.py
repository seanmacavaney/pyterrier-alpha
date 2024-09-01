"""This module provides utilities for working with Google Colab."""
import urllib.parse
from base64 import urlsafe_b64encode
from typing import Optional, Tuple

import lz4.block

_MAX_URL_LEN = 2000 # rough limit for most browsers
_BADGE_URL = 'https://colab.research.google.com/assets/colab-badge.svg'
_URL_TEMPLATE = 'https://colaburl.uk/{enc_code}{notebook_param}'


def _code_encode_b64(code: str) -> str:
    code = code.strip().encode()
    return urlsafe_b64encode(code).decode()


def _code_encode_lz4(code: str) -> str:
    code = code.strip().encode()
    return urlsafe_b64encode(lz4.block.compress(code, mode='high_compression')).decode()


def _code_encode(code: str) -> Tuple[str, str]:
    b64_enc = _code_encode_b64(code)
    if len(b64_enc) > 100: # try compression instead
        lz4_enc = _code_encode_lz4(code)
        if len(lz4_enc) < len(b64_enc): # it worked!
            return lz4_enc, 'py.lz4'
    return b64_enc, 'py.b64'


def code_url(
    code: str,
    notebook_name: Optional[str] = None,
    *,
    error_long: bool = True,
) -> str:
    """Generate a Colab URL from a code string.

    Args:
        code: The code to encode.
        notebook_name: The name of the notebook.
        error_long: Whether to raise an error if the generated URL is too long.
    """
    enc_code, fmt = _code_encode(code)
    if fmt == 'py.b64':
        enc_code = f'{enc_code}.b64'
    elif fmt == 'py.lz4':
        enc_code = f'{enc_code}.lz4'
    else:
        raise ValueError()

    if notebook_name:
        notebook_param = '?name=' + urllib.parse.quote_plus(notebook_name)
    else:
        notebook_param = ''

    url = _URL_TEMPLATE.format(enc_code=enc_code, notebook_param=notebook_param)

    if error_long and len(url) > _MAX_URL_LEN:
        raise ValueError('Your code is too long to encode in a URL.')

    return url


def code_html_link(
    code: str,
    notebook_name: Optional[str] = None,
    *,
    error_long: bool = True
) -> str:
    """Generate a Colab HTML link element from a code string.

    Args:
        code: The code to encode.
        notebook_name: The name of the notebook.
        error_long: Whether to raise an error if the generated URL is too long.
    """
    _url = code_url(code, notebook_name, error_long=error_long)
    return f'<a href="{_url}" rel="nofollow" target="_blank" class="colaburl">' \
           f'<img src="{_BADGE_URL}" alt="Open In Colab" style="margin: 0; display: inline-block;" /></a>'

def code_html_form(
    code: str,
    notebook_name: Optional[str] = None,
) -> str:
    """Generate a Colab HTML form element from a code string.

    Args:
        code: The code to encode.
        notebook_name: The name of the notebook.
    """
    enc_code, fmt = _code_encode(code)
    if notebook_name:
        notebook_param = '?name=' + urllib.parse.quote_plus(notebook_name)
    else:
        notebook_param = ''
    _url = _URL_TEMPLATE.format(enc_code='', notebook_param=notebook_param)
    return f'<form action="{_url}" method="POST" class="colaburl">' \
           f'<input type="hidden" name="{fmt}" value="{enc_code}">' \
           f'<input type="image" src="{_BADGE_URL}">' \
           '</form>'


def code_html(
    code: str,
    notebook_name: Optional[str] = None,
) -> str:
    """Generate a Colab HTML element from a code string, either as a link or a form, depending on the code length."""
    try:
        return code_html_link(code, notebook_name)
    except ValueError:
        return code_html_form(code, notebook_name)
