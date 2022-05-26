from pywebio.session import *
from pywebio.session import get_current_session

__all__ = ['get_all_query', 'get_query', 'set_localstorage', 'get_localstorage', 'set_cookie', 'get_cookie']


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
