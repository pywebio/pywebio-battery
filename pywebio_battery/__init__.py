"""
``pywebio_battery`` --- PyWebIO battery
=========================================

*Utilities that help write PyWebIO apps quickly and easily.*

.. note::
   ``pywebio_battery`` is an extension package of PyWebIO, you must install it before using it.
   To install this package, run ``pip3 install -U pywebio-battery``

Functions list
-----------------


Interaction related
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::

   * - Function name
     - Description

   * - `confirm <pywebio_battery.confirm>`
     - Confirmation modal

   * - `popup_input <pywebio_battery.popup_input>`
     - Show a form in popup window

   * - `redirect_stdout <pywebio_battery.redirect_stdout>`
     - redirecting stdout to pywebio

   * - `run_shell <pywebio_battery.run_shell>`
     - Run command in shell

   * - `put_logbox <pywebio_battery.put_logbox>`, `logbox_append <pywebio_battery.logbox_append>`
     - Logbox widget


Web application related
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::

   * - Function name
     - Description

   * - `get_all_query <pywebio_battery.get_all_query>`, `get_query <pywebio_battery.get_query>`
     - Get URL parameter

   * - `set_localstorage <pywebio_battery.set_localstorage>`, `get_localstorage <pywebio_battery.get_localstorage>`
     - User browser storage

   * - `set_cookie <pywebio_battery.set_cookie>`, `get_cookie <pywebio_battery.get_cookie>`
     - Web Cookie

   * - `login <pywebio_battery.login>`
     - Authentication

"""
from .interaction import *
from .web import *
from .interaction import __all__ as interaction_all
from .web import __all__ as web_all

__all__ = interaction_all + web_all

# Set default logging handler to avoid "No handler found" warnings.
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())
del logging
