import time
from subprocess import Popen
from playwright.sync_api._generated import Browser, BrowserContext, Page
import util
from pywebio_battery import *
from pywebio.output import *
from pywebio.pin import *


def target():
    ######### confirm
    res = confirm('confirmation modal', [
        put_markdown('~~del~~').style('color:red'),
        put_table([
            ['A', 'B'],
            ['C', put_text('Red').style('color:red')],
        ])
    ])
    assert res is True
    res = confirm('cancel test', put_text('cancel'))
    assert res is False
    res = confirm('timeout test', put_text('wait for timeout...'), timeout=3)
    assert res is None

    ######### popup_input
    res = popup_input([
        put_input('input', label='input'),
        put_textarea('textarea', label='textarea', rows=3, code=None, placeholder='placeholder', readonly=False, ),
    ])
    assert res == {
        'input': 'input',
        'textarea': 'textarea',
    }

    ######### popup_input
    with redirect_stdout():
        print('redirect_stdout')

    ######### run_shell
    run_shell("""python3 -c 'print("hello world")'""")

    ######### put_logbox,logbox_append
    put_logbox('log')
    for i in range(10):
        logbox_append('log', str(i) * 10 + '\n')

    put_text('All test passed')


def test(server_proc: Popen, browser: Browser, context: BrowserContext, page: Page):
    # Click button:has-text("CONFIRM")
    page.locator("button:has-text(\"CONFIRM\")").click()
    time.sleep(1)

    # Click button:has-text("CANCEL")
    page.locator("button:has-text(\"CANCEL\")").click()

    time.sleep(5)  # wait for modal timeout

    # Click input[name="input"]
    page.locator("input[name=\"input\"]").click()
    # Fill input[name="input"]
    page.locator("input[name=\"input\"]").fill("input")
    # Press Tab
    page.locator("input[name=\"input\"]").press("Tab")
    # Fill textarea[name="textarea"]
    page.locator("textarea[name=\"textarea\"]").fill("textarea")
    # Click text=Submit
    page.locator("text=Submit").click()

    time.sleep(1)
    assert 'redirect_stdout' in page.inner_text('body')
    assert 'All test passed' in page.inner_text('body')


if __name__ == '__main__':
    util.run_test(test, pywebio_app=target)
