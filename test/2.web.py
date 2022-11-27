import time
from subprocess import Popen
from playwright.sync_api._generated import Browser, BrowserContext, Page
import util
from pywebio_battery import *
from pywebio.output import *
from pywebio.session import eval_js, run_js


def target():
    if get_query('a'):
        assert get_query('a') == '1'
        assert 'b' in get_all_query()
        assert get_localstorage('pywebio') == 'awesome'
        assert get_cookie('pywebio') == 'awesome'

        put_text('All test passed')
        return

    set_localstorage('pywebio', 'awesome')
    set_cookie('pywebio', 'awesome')
    user = basic_auth(lambda u, p: u == p == 'pywebio', secret='secret')
    assert user == 'pywebio'

    url = eval_js('window.location.href')
    if '?' in url:
        url += '&a=1&b=2&c=3'
    else:
        url += '?a=1&b=2&c=3'

    run_js('window.location.href=url', url=url)


def test(server_proc: Popen, browser: Browser, context: BrowserContext, page: Page):
    # Click input[name="username"]
    page.locator("input[name=\"username\"]").click()
    # Fill input[name="username"]
    page.locator("input[name=\"username\"]").fill("pywebio")

    page.locator("input[name=\"password\"]").click()
    # Fill input[name="password"]
    page.locator("input[name=\"password\"]").fill("pywebio")
    # Click text=Submit
    # with page.expect_navigation(url="http://127.0.0.1:8080/?a=1&b=2&c=3"):
    with page.expect_navigation():
        page.locator("text=Submit").click()

    time.sleep(1)
    assert 'All test passed' in page.inner_text('body')


if __name__ == '__main__':
    util.run_test(test, pywebio_app=target)
