from pywebio.input import *
from pywebio.output import *
from pywebio.session import *
from pywebio.session import get_current_session
from tornado.web import create_signed_value, decode_signed_value
from typing import *

__all__ = ['get_all_query', 'get_query', 'set_localstorage', 'get_localstorage', 'set_cookie', 'get_cookie',
           'basic_auth', 'custom_auth', 'revoke_auth']


def get_all_query():
    """Get URL parameter (also known as "query strings" or "URL query parameters") as a dict"""
    query = eval_js("Object.fromEntries(new URLSearchParams(window.location.search))")
    return query


def get_query(name):
    """Get URL parameter value"""
    query = eval_js("new URLSearchParams(window.location.search).get(n)", n=name)
    return query


def set_localstorage(key, value):
    """Save data to user's web browser

    The data is specific to the origin (protocol+domain+port) of the app.
    Different origins use different web browser local storage.

    :param str key: the key you want to create/update.
    :param str value: the value you want to give the key you are creating/updating.

    You can read the value by using :func:`get_localstorage(key) <get_localstorage>`
    """
    run_js("localStorage.setItem(key, value)", key=key, value=value)


def get_localstorage(key) -> str:
    """Get the key's value in user's web browser local storage"""
    return eval_js("localStorage.getItem(key)", key=key)


def _init_cookie_client():
    session = get_current_session()
    if 'cookie_client_flag' not in session.internal_save:
        session.internal_save['cookie_client_flag'] = True
        # Credit: https://stackoverflow.com/questions/14573223/set-cookie-and-get-cookie-with-javascript
        run_js("""
        window.setCookie = function(name,value,days) {
            var expires = "";
            if (days) {
                var date = new Date();
                date.setTime(date.getTime() + (days*24*60*60*1000));
                expires = "; expires=" + date.toUTCString();
            }
            document.cookie = name + "=" + (value || "")  + expires + "; path=/";
        }
        window.getCookie = function(name) {
            var nameEQ = name + "=";
            var ca = document.cookie.split(';');
            for(var i=0;i < ca.length;i++) {
                var c = ca[i];
                while (c.charAt(0)==' ') c = c.substring(1,c.length);
                if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
            }
            return null;
        }
        """)


def set_cookie(key, value, days=7):
    """Set cookie"""
    _init_cookie_client()
    run_js("setCookie(key, value, days)", key=key, value=value, days=days)


def get_cookie(key):
    """Get cookie"""
    _init_cookie_client()
    return eval_js("getCookie(key)", key=key)


def basic_auth(verify_func: Callable[[str, str], bool], secret: Union[str, bytes],
               expire_days=7, token_name='pywebio_auth_token') -> str:
    """Persistence authentication with username and password.

    You need to provide a function to verify the current user based on username and password. The ``basic_auth()``
    function will save the authentication state in the user's web browser, so that the authed user does not need
    to log in again.

    :param callable verify_func: User authentication function. It should receive two arguments: username and password.
        If the authentication is successful, it should return ``True``, otherwise return ``False``.
    :param str secret: HMAC secret for the signature. It should be a long, random str.
    :param int expire_days: how many days the auth state can keep valid.
       After this time, authed users need to log in again.
    :param str token_name: the name of the token to store the auth state in user browser.
    :return str: username of the current authed user

    Example:

    .. exportable-codeblock::
        :name: basic_auth
        :summary: Persistence authentication with username and password

        user_name = basic_auth(lambda username, password: username == 'admin' and password == '123',
                               secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__")
        put_text("Hello, %s. You can refresh this page and see what happen" % user_name)

    """

    token = get_localstorage(token_name)  # get token from user's web browser
    # try to decrypt the username from the token
    username = decode_signed_value(secret, token_name, token, max_age_days=expire_days)
    if username:
        username = username.decode('utf8')
    if not token or not username:  # no token or token validation failed
        while True:
            user = input_group('Login', [
                input("Username", name='username'),
                input("Password", type=PASSWORD, name='password'),
            ])
            username = user['username']
            ok = verify_func(username, user['password'])
            if ok:
                # encrypt username to token
                signed = create_signed_value(secret, token_name, username).decode("utf-8")
                set_localstorage(token_name, signed)  # set token to user's web browser
                break
            else:
                toast('Username or password is incorrect', color='error')

    return username


def custom_auth(login_func: Callable[[], str], secret=Union[str, bytes], expire_days=7,
                token_name='pywebio_auth_token') -> str:
    """Persistence authentication with custom logic.

    You need to provide a function to determine the current user and return the username. The ``custom_auth()``
    function will save the authentication state in the user's web browser, so that the authed user does not need
    to log in again.

    :param callable login_func: User login function. It should receive no arguments and return the username of the
        current user. If fail to verify the current user, it should return ``None``.
    :param str secret: HMAC secret for the signature. It should be a long, random str.
    :param int expire_days: how many days the auth state can keep valid.
       After this time,authed users need to log in again.
    :param str token_name: the name of the token to store the auth state in user browser.
    :return str: username of the current authed user
    """

    token = get_localstorage(token_name)  # get token from user's web browser
    # try to decrypt the username from the token
    username = decode_signed_value(secret, token_name, token, max_age_days=expire_days)
    if username:
        username = username.decode('utf8')
    if not token or not username:  # no token or token validation failed
        while True:
            username = login_func()
            if username:
                # encrypt username to token
                signed = create_signed_value(secret, token_name, username).decode("utf-8")
                set_localstorage(token_name, signed)  # set token to user's web browser
                break
            else:
                toast('Authentication failed', color='error')

    return username


def revoke_auth(token_name='pywebio_auth_token'):
    """Revoke the auth state of current user

    :param str token_name: the name of the token to store the auth state in user browser.
    """
    set_localstorage(token_name, '')
