from __future__ import annotations

"""Central place to obtain the Jinja2Templates instance.

Re-exports the single instance already created in ``appgenesis.core`` instead
of instantiating a second ``Jinja2Templates`` — creating a second instance
would maintain its own template cache/globals and could drift from the one
`appgenesis/app.py` actually renders with.
"""

from appgenesis.core import templates

__all__ = ["templates"]
