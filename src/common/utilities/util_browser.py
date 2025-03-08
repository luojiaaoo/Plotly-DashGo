from flask import request
from user_agents import parse
from typing import Literal, Optional
from dataclasses import dataclass

browser_type = Literal['Chrome', 'Firefox', 'Safari', 'IE', 'Edge', 'Opera', 'Other']


@dataclass
class BrowserInfo:
    type: browser_type
    version: Optional[int]
    ip: str


def get_browser_info() -> BrowserInfo:
    request_addr = request.remote_addr
    user_string = str(request.user_agent)
    user_agent = parse(user_string)
    bw: browser_type = user_agent.browser.family
    version: Optional[int] = user_agent.browser.version[0] if user_agent.browser.version else None
    return BrowserInfo(type=bw.lower(), version=version, ip=request_addr)
