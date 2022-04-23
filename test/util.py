import asyncio
import os
import signal
import subprocess
import sys
import time
from urllib.parse import urlparse
import pywebio
from playwright.sync_api import Playwright, sync_playwright
import requests
from pywebio.utils import wait_host_port, get_free_port

USAGE = """
python {name} 
    启动PyWebIO服务器

python {name} auto
    使用无头浏览器进行自动化测试，并使用coverage检测代码覆盖率

python {name} debug
    使用带界面的浏览器自动化测试
"""
default_chrome_options = {'headless': False}


def run_test(test_func, pywebio_app=None, start_server=None, address='http://localhost:8080?_pywebio_debug=1',
             chrome_options=None):
    """
    :param test_func: 测试的函数。人工测试时不会被运行 (server_proc, browser, context, page)
    :param pywebio_app: PyWebIO app
    :param start_server: 启动PyWebIO服务器的函数
    """
    if len(sys.argv) not in (1, 2) or (len(sys.argv) == 2 and sys.argv[-1] not in ('server', 'auto', 'debug')):
        print(USAGE.format(name=sys.argv[0]))
        return

    if len(sys.argv) != 2:  # when execute test script with no argument, only start server
        try:
            if pywebio_app:
                # pywebio.enable_debug()
                port = int(os.environ.get('PORT', 8080))
                pywebio.start_server(pywebio_app, port=port, host='127.0.0.1', cdn=False, debug=True)
            else:
                start_server()
        except KeyboardInterrupt:
            pass
        sys.exit()

    if chrome_options is None:
        chrome_options = default_chrome_options

    port = 8080
    if pywebio_app:
        port = get_free_port()
        address = f'http://localhost:{port}?_pywebio_debug=1'

    proc = None
    env = dict(os.environ)
    env['PORT'] = str(port)
    if sys.argv[-1] == 'auto':
        chrome_options['headless'] = True
        proc = subprocess.Popen(['coverage', 'run', '--source', 'pywebio_battery', '--append',
                                 sys.argv[0]], stdout=sys.stdout, stderr=subprocess.STDOUT, text=True, env=env)
    elif sys.argv[-1] == 'debug':
        # start server as sub process
        proc = subprocess.Popen([sys.executable, sys.argv[0]], stdout=sys.stdout,
                                stderr=subprocess.STDOUT, text=True, env=env)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**chrome_options)
        context = browser.new_context()
        try:
            # Open new page
            page = context.new_page()
            # browser.set_window_size(1000, 900)
            for _ in range(20):
                try:
                    requests.get(address, timeout=1)
                    break
                except Exception as e:
                    pass
                time.sleep(1)
            page.goto(address)
            test_func(proc, browser, context, page)
        finally:
            if sys.argv[-1] == 'debug':
                input('press ENTER to exit')
                proc.terminate()
            context.close()
            browser.close()

        # 不要使用 proc.terminate() ，因为coverage会无法保存分析数据
        proc.send_signal(signal.SIGINT)
        print("Closed browser and PyWebIO server")
