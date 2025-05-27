from fastapi import HTTPException
from typing import Optional
import os

CLICK_SCRIPT = """
function handleClickAndRemove(link) {
    const element = document.getElementById('ad-fad0d3586a29d80b4745f0fee402a64f392536a9');
    if (element) {
        element.parentNode.removeChild(element);
    }

    fetch(link)
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Ad closing failed');
            }
        })
        .then(data => {
            console.log('Ad closing successful:', data);
        })
        .catch(error => {
            console.error('Ad closing failed:', error);
        });
};
"""


async def get_ad_html(
    ad_id: str,
    link: Optional[str] = None,
    site: Optional[str] = None,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    content: Optional[str] = None,
    btntext: Optional[str] = None,
    imgalt: Optional[str] = None,
    imgpath: Optional[str] = None,
    server: Optional[str] = None,
    port: Optional[str] = None,
):
    file_path = os.path.join("./html", f"{ad_id}.html")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_path, "r", encoding="utf-8") as file:
        html = file.read()

    replacements = {
        "[LINK]": link if link else "",
        "[SITE]": site if site else "",
        "[TITLE]": title if title else "",
        "[SUBTITLE]": subtitle if subtitle else "",
        "[CONTENT]": content if content else "",
        "[BTNTEXT]": btntext if btntext else "",
        "[IMGALT]": imgalt if imgalt else "",
        "[IMGPATH]": imgpath if imgpath else "",
        "[SERVER]": server if server else "",
        "[PORT]": port if port else "",
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    return html
