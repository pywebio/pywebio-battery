"""
``pywebio_battery`` --- PyWebIO battery
=========================================

*Utilities that help write PyWebIO apps quickly and easily.*

.. note::
   ``pywebio_battery`` is an extension package of PyWebIO, you must install it before using it.
   To install this package, run ``pip3 install -U pywebio-battery``

Functions index
-----------------


Interaction related
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::

   * - Function name
     - Description

   * - `file_picker <pywebio_battery.file_picker>`
     - Local file picker

   * - `confirm <pywebio_battery.confirm>`
     - Confirmation modal

   * - `popup_input <pywebio_battery.popup_input>`
     - Show a form in popup window

   * - `redirect_stdout <pywebio_battery.redirect_stdout>`
     - redirecting stdout to pywebio

   * - `run_shell <pywebio_battery.run_shell>`
     - Run command in shell

   * - `put_logbox <pywebio_battery.put_logbox>`, `logbox_append <pywebio_battery.logbox_append>`, `logbox_clear <pywebio_battery.logbox_clear>`
     - Logbox widget

   * - `put_video <pywebio_battery.put_video>`
     - Output video

   * - `put_audio <pywebio_battery.put_audio>`
     - Output audio
   
   * - `wait_scroll_to_bottom <pywebio_battery.wait_scroll_to_bottom>`
     - Wait the page is scrolled to bottom

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

   * - `basic_auth <pywebio_battery.basic_auth>`, `custom_auth <pywebio_battery.custom_auth>`,
       `revoke_auth <pywebio_battery.revoke_auth>`
     - Authentication

"""
from .interaction import *
from .web import *
from .file_picker import file_picker

# make Sphinx can auto generate API docs for this package
from .interaction import __all__ as interaction_all
from .web import __all__ as web_all

__all__ = ['file_picker'] + interaction_all + web_all
