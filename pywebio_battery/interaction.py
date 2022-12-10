import base64
import html
import io
import subprocess
from functools import partial
from typing import Union, Optional, Sequence

from pywebio.output import *
from pywebio.output import Output
from pywebio.output import OutputPosition
from pywebio.pin import *
from pywebio.session import *
from pywebio.utils import random_str

__all__ = ['confirm', 'popup_input', 'redirect_stdout', 'run_shell', 'put_logbox', 'logbox_append', 'put_video',
           'put_audio']


def confirm(
        title: str,
        content: Union[str, Output, Sequence[Union[str, Output]]] = None,
        *,
        timeout: int = None
) -> Optional[bool]:
    """Show a confirmation modal.

    :param str title: Model title.
    :param list/put_xxx()/str content: The content of the confirmation modal.
        Can be a string, the put_xxx() calls , or a list of them.
    :param None/float timeout: Seconds for operation time out.
    :return: Return `True` when the "CONFIRM" button is clicked,
        return `False` when the "CANCEL" button is clicked,
        return `None` when a timeout is given and the operation times out.

    .. exportable-codeblock::
        :name: battery-confirm
        :summary: Blocking confirmation modal

        from pywebio_battery import confirm  # ..demo-only
        # ..demo-only
        choice = confirm("Delete File", "Are you sure to delete this file?")
        put_text("Your choice", choice)
    """
    if content is None:
        content = []
    if not isinstance(content, list):
        content = [content]
    action_name = random_str(10)

    content.append(put_actions(action_name, buttons=[
        {'label': 'CONFIRM', 'value': True},
        {'label': 'CANCEL', 'value': False, 'color': 'danger'},
    ]).style('margin-top: 1rem; float: right;'))
    popup(title=title, content=content, closable=False)
    result = pin_wait_change(action_name, timeout=timeout)
    if result:
        result = result['value']
    close_popup()
    return result


def popup_input(
        pins: Sequence[Output],
        title='Please fill out the form below'
) -> Optional[dict]:
    """Show a form in popup window.

    :param list pins: :doc:`pin </pin>` widget list. It can also contain ordinary output widgets.
    :param str title: model title.
    :return: return the form value as dict, return ``None`` when user cancel the form.

    .. exportable-codeblock::
        :name: battery-popup-input
        :summary: Blocking form in the popup.

        from pywebio_battery import popup_input  # ..demo-only
        # ..demo-only
        form = popup_input([
            put_input("username", label="User name"),
            put_input("password", type=PASSWORD, label="Password"),
            put_info("If you forget your password, please contact the administrator."),
        ], "Login")
        put_text("Login info:", form)
    """
    if not isinstance(pins, list):
        pins = [pins]

    pin_names = [
        p.spec['input']['name']
        for p in pins
        if 'input' in p.spec and 'name' in p.spec['input']
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


def run_shell(cmd: str, output_func=partial(put_text, inline=True), encoding='utf8') -> int:
    """Run command in shell and output the result to pywebio

    :param str cmd: command to run
    :param callable output_func: output function, default to `put_text()`.
        the function should accept one argument, the output text of command.
    :param str encoding: command output encoding
    :return: shell command return code

    .. versionchanged:: 0.4
       add ``encoding`` parameter and return code
    """
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        while True:
            out = process.stdout.readline()
            if out:
                output_func(out.decode(encoding))

            if not out and process.poll() is not None:
                break
    finally:
        process.kill()
        process.stdout.close()
    return process.poll()


def put_logbox(name: str, height=400, keep_bottom=True) -> Output:
    r"""Output a logbox widget

    .. exportable-codeblock::
        :name: battery-put-logbox
        :summary: Logbox widget

        from pywebio_battery import put_logbox, logbox_append   # ..demo-only
        # ..demo-only
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


def logbox_append(name: str, text: str):
    """Append text to a logbox widget"""
    run_js('$("#webio-logbox-%s").append(document.createTextNode(text))' % name, text=str(text))


def put_video(src: Union[str, bytes], autoplay: bool = False, loop: bool = False,
              height: int = None, width: int = None, muted: bool = False, poster: str = None,
              scope: str = None, position: int = OutputPosition.BOTTOM) -> Output:
    """Output video

    :param str/bytes src: Source of video. It can be a string specifying video URL, a bytes-like object specifying
        the binary content of the video.
    :param bool autoplay: Whether to autoplay the video.
        In some browsers (e.g. Chrome 70.0) autoplay doesn't work if not enable ``muted``.
    :param bool loop: If True, the browser will automatically seek back to the start upon reaching the end of the video.
    :param int width: The width of the video's display area, in CSS pixels. If not specified, the intrinsic width of
        the video is used.
    :param int height: The height of the video's display area, in CSS pixels. If not specified, the intrinsic height of
        the video is used.
    :param bool muted: If set, the audio will be initially silenced.
    :param str poster: A URL for an image to be shown while the video is downloading. If this attribute isn't specified,
        nothing is displayed until the first frame is available, then the first frame is shown as the poster frame.
    :param int scope, position: Those arguments have the same meaning as for :func:`put_text() <pywebio.output.put_text>`

    Example:

    .. exportable-codeblock::
        :name: put_video
        :summary: `put_video()` usage

        url = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"
        put_video(url)

    .. versionadded:: 0.4
    """
    kwargs = locals()
    if isinstance(src, (bytes, bytearray)):
        src = 'data:video/mp4;base64, ' + base64.b64encode(src).decode('ascii')

    tag_fields = ['autoplay', 'loop', 'muted']
    tags = ' '.join(t for t in tag_fields if kwargs[t])
    value_fields = ['height', 'width', 'poster']

    values = ' '.join('%s="%s"' % (k, html.escape(kwargs[k], quote=True))
                      for k in value_fields if kwargs[k] is not None)

    tag = r'<video src="{src}" controls {tags} {values} preload="metadata"><video/>'.format(
        src=src, tags=tags, values=values)
    return put_html(tag, scope=scope, position=position)


def put_audio(src: Union[str, bytes], autoplay: bool = False, loop: bool = False,
              muted: bool = False, scope: str = None, position: int = OutputPosition.BOTTOM) -> Output:
    """Output audio

    :param str/bytes src: Source of audio. It can be a string specifying video URL, a bytes-like object specifying
        the binary content of the audio.
    :param bool autoplay: Whether to autoplay the audio.
    :param bool loop: If True, the browser will automatically seek back to the start upon reaching the end of the audio.
    :param bool muted: If set, the audio will be initially silenced.
    :param scope: The scope of the video. It can be ``"session"`` or ``"page"``. If not specified,
        the video will be automatically removed when the session is closed.
    :param int scope, position: Those arguments have the same meaning as for :func:`put_text() <pywebio.output.put_text>`

    Example:

    .. exportable-codeblock::
        :name: put_audio
        :summary: `put_audio()` usage

        url = "https://interactive-examples.mdn.mozilla.net/media/cc0-audio/t-rex-roar.mp3"
        put_audio(url)

    .. versionadded:: 0.4
    """
    kwargs = locals()
    if isinstance(src, (bytes, bytearray)):
        src = 'data:audio/wav;base64, ' + base64.b64encode(src).decode('ascii')

    tag_fields = ['autoplay', 'loop', 'muted']
    tags = ' '.join(t for t in tag_fields if kwargs[t])

    tag = r'<audio src="{src}" {tags} controls preload="metadata"><audio/>'.format(src=src, tags=tags)
    return put_html(tag, scope=scope, position=position)
