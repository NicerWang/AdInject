import json
import os
import requests

AD_SERVER = os.environ.get("AD_SERVER", "localhost")
AD_SERVER_PORT = os.environ.get("AD_SERVER_PORT", "61234")
AD_PATH = os.environ.get("AD_PATH", "ad.json")
AD_ID = os.environ.get("AD_ID", "01")
AD_STYLE = os.environ.get("AD_STYLE", "popup")
AD_SCALE = float(os.environ.get("AD_SCALE", 1.0))
AD_ENHANCE = os.environ.get("AD_ENHANCE", None)
AD_ENABLE = os.environ.get("AD_ENABLE", None)

ad_content = json.loads(open(AD_PATH).read())

ad_config = {
    "link": f"http://{AD_SERVER}:{AD_SERVER_PORT}/close_ad",
    "site": "",
    "title": ad_content["title"],
    "subtitle": "",
    "content": ad_content["content"],
    "btntext": ad_content["button_text"],
    "imgalt": "",
    "imgpath": "",
    "server": AD_SERVER,
    "port": AD_SERVER_PORT,
    "style": AD_STYLE,
    "scale": AD_SCALE
}


def request_ad_server(is_start: bool, tag: str = None, **kwargs) -> None:
    if AD_ENABLE is not None:
        return True
    assert (
        is_start and tag is not None
    ) or not is_start, "tag must be provided when is_start is True"

    ad_config.update(kwargs)
    if AD_ENHANCE is not None:
        ad_config["enhance"] = "true"

    if is_start:
        url = f"http://{AD_SERVER}:{AD_SERVER_PORT}/start_cdp_injection/{tag}/{AD_ID}"
        response = requests.get(url, params=ad_config)
    else:
        url = f"http://{AD_SERVER}:{AD_SERVER_PORT}/close_ad?finished=true"
        response = requests.get(url)

    if response.status_code == 200:
        return True
    else:
        return False


def count_step():
    if AD_ENABLE is not None:
        return True
    url = f"http://{AD_SERVER}:{AD_SERVER_PORT}/step"
    response = requests.get(url)
    if response.status_code == 200:
        return True
    else:
        return False