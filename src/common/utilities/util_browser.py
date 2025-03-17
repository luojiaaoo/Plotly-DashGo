from flask import request
from user_agents import parse
from typing import Literal, Optional
from dataclasses import dataclass
from config.dashgo_conf import ProxyConf

browser_type = Literal['chrome', 'firefox', 'safari', 'ie']


@dataclass
class BrowserInfo:
    url: str
    type: browser_type
    version: Optional[int]
    request_addr: str


def get_browser_info() -> BrowserInfo:
    # 取代理链的第一个IP为用户IP
    request_addr = request.headers.get('X-Forwarded-For').split(',')[0] if ProxyConf.NGINX_PROXY else request.remote_addr
    user_string = str(request.user_agent)
    user_agent = parse(user_string)
    bw: browser_type = user_agent.browser.family
    version: Optional[int] = user_agent.browser.version[0] if user_agent.browser.version else None
    return BrowserInfo(type=bw.lower(), version=version, request_addr=request_addr, url=request.url)
