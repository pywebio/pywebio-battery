from pywebio.output import *
from pywebio.input import *
from pywebio.session import *
from pywebio.pin import *
from pywebio.utils import random_str
from pywebio.output import Output
import io
from functools import partial
import subprocess

__all__ = ['confirm', 'popup_input', 'redirect_stdout', 'run_shell', 'put_logbox', 'logbox_append']


def confirm(title, content=None, *, timeout=None):
    """Show a confirmation modal.

    :param str title: Model title.
    :param list/put_xxx() content: Model content.
    :param None/float timeout: Seconds for operation time out.
    :return: Return `True` when the "CONFIRM" button is clicked,
        return `False` when the "CANCEL" button is clicked,
        return `None` when a timeout is given and the operation times out.
    """
    if content is None:
        content = []
    if not isinstance(content, list):
        content = [content]
    action_name = random_str(10)
    content.append(put_actions(action_name, buttons=[
        {'label': 'CONFIRM', 'value': True},
        {'label': 'CANCEL', 'value': False, 'color': 'danger'},
    ]))
    popup(title=title, content=content, closable=False)
    result = pin_wait_change(action_name, timeout=timeout)
    if result:
        result = result['value']
    close_popup()
    return result


def popup_input(pins, title='Please fill out the form below'):
    """Show a form in popup window.

    :param list pins: pin output list.
    :param str title: model title.
    :return: return the form value as dict, return None when user cancel the form.
    """
    if not isinstance(pins, list):
        pins = [pins]

    pin_names = [
        p.spec['input']['name']
        for p in pins
    ]
    action_name = 'action_' + random_str(10)
    pins.append(put_actions(action_name, buttons=[
        {'label': 'Submit', 'value': True},
        {'label': 'Cancel', 'value': False, 'color': 'danger'},
    ]))
    popup(title=title, content=pins, closable=False)

    change_info = pin_wait_change(action_name)
    result = None
    if change_info['name'] == action_name and change_info['value']:
        result = {name: pin[name] for name in pin_names}
    close_popup()
    return result


def redirect_stdout(output_func=partial(put_text, inline=True)):
    """Context manager for temporarily redirecting stdout to pywebio.

    ::

        with redirect_stdout():
            print("Hello world.")
    """
    from contextlib import redirect_stdout

    class WebIO(io.IOBase):
        def write(self, content):
            output_func(content)

    return redirect_stdout(WebIO())


def run_shell(cmd, output_func=partial(put_text, inline=True)):
    """Run command in shell and output the result to pywebio"""
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        out = process.stdout.readline()
        if out:
            output_func(out.decode('utf8'))

        if not out and process.poll() is not None:
            break


def put_logbox(name, height=400, keep_bottom=True) -> Output:
    r"""Output a logbox widget

    ::

        import time

        put_logbox("log")
        while True:
            logbox_append("log", f"{time.time()}\n")
            time.sleep(0.2)

    :param str name: the name of the widget, must unique in session-wide.
    :param int height: the height of the widget in pixel
    :param bool keep_bottom: Whether to scroll to bottom when new content is appended
        (via `logbox_append()`).

    .. versionchanged:: 0.3
       add ``keep_bottom`` parameter
    """
    dom_id = "webio-logbox-%s" % name
    style = 'height:%spx' % height if height else ''
    html = '<pre style="%s" tabindex="0"><code id="%s"></code></pre>' % (style, dom_id)
    if keep_bottom:
        html += """
         <script>
             (function(){
                 let div = document.getElementById(%r).parentElement, stop=false;
                 $(div).on('focusin', function(e){ stop=true }).on('focusout', function(e){ stop=false });;
                 new MutationObserver(function (mutations, observe) {
                     if(!stop) $(div).stop().animate({ scrollTop: div.scrollHeight}, 300);
                 }).observe(div, { childList: true, subtree:true });
             })();
         </script>
         """ % dom_id
    return put_html(html)


def logbox_append(name, text):
    """Append text to a logbox widget"""
    run_js('$("#webio-logbox-%s").append(document.createTextNode(text))' % name, text=str(text))
