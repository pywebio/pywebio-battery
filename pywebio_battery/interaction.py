import base64
import html
import io
import subprocess
from functools import partial
from typing import Union, Optional, Sequence, Mapping, Tuple, Callable, Dict

from pywebio.output import *
from pywebio.output import Output
from pywebio.output import OutputPosition
from pywebio.pin import *
from pywebio.session import *
from pywebio.utils import random_str

__all__ = ['confirm', 'popup_input', 'redirect_stdout', 'run_shell', 'put_logbox', 'logbox_append', 'logbox_clear', 
           'put_video', 'put_audio', 'wait_scroll_to_bottom']


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
        pins: Union[Sequence[Output], Output],
        title='Please fill out the form below',
        validate: Callable[[Dict], Optional[Tuple[str, str]]] = None,
        popup_size: str = PopupSize.NORMAL,
        cancelable: bool = False
) -> Optional[dict]:
    """Show a form in popup window.

    :param list pins: :doc:`pin </pin>` widget list. It can also contain ordinary output widgets.
    :param str title: model title.
    :param callable validate: validation function for the form.
        Same as ``validate`` parameter in :func:`input_group() <pywebio.input.input_group()>`
    :param str popup_size: popup window size. See ``size`` parameter of :func:`popup() <pywebio.output.popup()>`
    :param bool cancelable: Whether the form can be cancelled. Default is ``False``.
        If ``cancelable=True``, a "Cancel" button will be displayed at the bottom of the form.
    :return: return the form value as dict, return ``None`` when user cancel the form.

    .. exportable-codeblock::
        :name: battery-popup-input
        :summary: Blocking form in the popup.

        from pywebio_battery import popup_input  # ..demo-only
        # ..demo-only
        def check_password(form):
            if len(form['password']) < 6:
                return 'password', 'password length must greater than 6'

        form = popup_input(
            [
                put_input("username", label="Username"),
                put_input("password", type=PASSWORD, label="Password"),
                put_info("If you forget your password, please contact the administrator."),
            ],
            title="Login",
            validate=check_password
        )
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
    action_buttons = [{'label': 'Submit', 'value': True}]
    if cancelable:
        action_buttons.append({'label': 'Cancel', 'value': False, 'color': 'danger'})
    pins.append(put_actions(action_name, buttons=action_buttons))
    popup(title=title, content=pins, closable=False, size=popup_size)

    result = None
    previous_invalid_field = None
    while True:
        result = None
        change_info = pin_wait_change(action_name)  # wait Submit / Cancel button click
        if change_info and change_info['name'] == action_name:
            if not change_info['value']:  # Cancel button click
                break
            result = {name: pin[name] for name in pin_names}
            if not validate:
                break
            error_info = validate(result)
            if not error_info:
                break
            try:
                name, error_msg = error_info
            except Exception:
                raise ValueError("The `validate` function for popup_input() must "
                                 "return `(name, error_msg)` when validation failed.") from None
            pin_update(name, valid_status=False, invalid_feedback=error_msg)
            if previous_invalid_field and previous_invalid_field != name:
                pin_update(previous_invalid_field, valid_status=0)  # remove the previous invalid status
            previous_invalid_field = name

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

    .. exportable-codeblock::
        :name: battery-run-shell
        :summary: Run shell and output to code block

        cmd = "ls -l"
        put_logbox('shell_output')
        run_shell(cmd, output_func=lambda msg: logbox_append('shell_output', msg))
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


def logbox_clear(name: str):
    """Clear all contents of a logbox widget"""
    run_js('$("#webio-logbox-%s").empty()' % name)


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

      .. note::

        Web browsers typically don't allow autoplaying audio without user interaction. If you want to autoplay audio,
        one way is to call `put_audio(autoplay=True)` in a callback function of a button.
        See also: https://developer.mozilla.org/en-US/docs/Web/Media/Autoplay_guide

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


def wait_scroll_to_bottom(threshold: float = 10, timeout: float = None) -> bool:
    r"""Wait until the page is scrolled to bottom.

    This function is useful to achieve infinite scrolling.

    :param float threshold: If the distance (in pixels) of the browser's viewport from the bottom of the page is less
        than the threshold, it is considered to reach the bottom
    :param float timeout: Timeout in seconds. The maximum time to wait for the page to scroll to bottom.
        Default is None, which means no timeout.
    :return: Return ``True`` if the page is scrolled to bottom, return ``False`` only when timeout.

    Example:

    .. exportable-codeblock::
        :name: wait_scroll_to_bottom
        :summary: `wait_scroll_to_bottom()` usage

        put_text('This is long text. Scroll to bottom to continue.\n' * 100)
        while True:
            wait_scroll_to_bottom()
            put_text("New generated content\n"*20)

    .. versionadded:: 0.5
    """
    return eval_js("""
        (function(){
            if($(window).scrollTop() + window.innerHeight > $(document).height() - threshold) return true;
            return new Promise(function(resolve){
                $(window).on('scroll', function(e){
                    if($(window).scrollTop() + window.innerHeight > $(document).height() - threshold){
                        resolve(true);
                    }
                });
                if(timeout) setTimeout(function(){ resolve(false); }, timeout*1000);
            });
        })();
    """, threshold=threshold, timeout=timeout)
