from typing import Literal


POP_UP_STYLE = """
document.addEventListener('DOMContentLoaded', function() {
    const divBlkContainer = document.createElement('div');
    divBlkContainer.id = 'ad-fad0d3586a29d80b4745f0fee402a64f392536a9';
    divBlkContainer.style.position = 'fixed';
    divBlkContainer.style.bottom = '20px';
    divBlkContainer.style.right = '20px';
    divBlkContainer.style.width = '[WIDTH]px';
    divBlkContainer.style.display = 'block';
    divBlkContainer.style.zIndex = '1000';

    const divBlk = document.createElement('div');
    divBlk.innerHTML = `[HTML]`;
    divBlk.style.width = '100%';
    divBlk.style.height = '100%';
    divBlk.style.border = 'none';
    divBlk.style.backgroundColor = 'white';
    divBlk.style.transform = 'scale([SCALE])';
    divBlk.style.transformOrigin = '100% 100%';

    divBlkContainer.appendChild(divBlk);
    document.body.appendChild(divBlkContainer);
});
"""

HEADER_STYLE_1 = """
document.addEventListener('DOMContentLoaded', function() {
    const fatherDiv = document.querySelector('header');
    const divBlk = document.createElement('div');
    divBlk.id = 'ad-fad0d3586a29d80b4745f0fee402a64f392536a9';
    divBlk.innerHTML = `[HTML]`;
    divBlk.style.width = '100%';
    divBlk.style.border = 'none';
    divBlk.style.backgroundColor = 'white';

    fatherDiv.insertAdjacentElement('afterend', divBlk);
});
"""

HEADER_STYLE_2 = """
document.addEventListener('DOMContentLoaded', function() {
    const fatherDiv = document.querySelector('body');
    const divBlk = document.createElement('div');
    divBlk.id = 'ad-fad0d3586a29d80b4745f0fee402a64f392536a9';
    divBlk.innerHTML = `[HTML]`;
    divBlk.style.width = '100%';
    divBlk.style.border = 'none';
    divBlk.style.backgroundColor = 'white';

    fatherDiv.insertAdjacentElement('beforebegin', divBlk);
});
"""


HEADER_STYLE_3 = """
document.addEventListener('DOMContentLoaded', function() {
    const fatherDiv = document.querySelector('#mw-mf-viewport');
    const divBlk = document.createElement('div');
    divBlk.id = 'ad-fad0d3586a29d80b4745f0fee402a64f392536a9';
    divBlk.innerHTML = `[HTML]`;
    divBlk.style.width = '100%';
    divBlk.style.border = 'none';
    divBlk.style.backgroundColor = 'white';

    fatherDiv.insertAdjacentElement('afterbegin', divBlk);
});
"""

SIDE_STYLE = """
document.addEventListener('DOMContentLoaded', function() {
    const fatherDiv = document.querySelector('#sidebar');
    const divBlk = document.createElement('div');
    divBlk.id = 'ad-fad0d3586a29d80b4745f0fee402a64f392536a9';
    divBlk.innerHTML = `[HTML]`;
    divBlk.style.width = '100%';
    divBlk.style.border = 'none';
    divBlk.style.backgroundColor = 'white';

    fatherDiv.insertAdjacentElement('afterbegin', divBlk);
});
"""

header_style_mapping = {
    "classifieds": HEADER_STYLE_1,
    "shopping": HEADER_STYLE_1,
    "wiki": HEADER_STYLE_3,
    "reddit": HEADER_STYLE_2,
}

side_style_mapping = {
    "classifieds": SIDE_STYLE,
    "reddit": SIDE_STYLE,
}


def pop_up_style(
    width: int = 350,
    height: int = None,
    style_site_id: Literal["classified", "wiki", "shopping", "reddit"] = "reddit",
    scale: float = 1.0,
) -> str:
    assert height is None, "height is controlled by the content"

    return POP_UP_STYLE.replace("[WIDTH]", str(width)).replace("[SCALE]", str(scale))


def header_style(
    width: int = None,
    height: int = None,
    style_site_id: Literal["classified", "wiki", "shopping", "reddit"] = "reddit",
    scale: float = 1.0,
) -> str:
    assert width is None, "width is the screen size"
    assert height is None, "height is controlled by the content"
    if style_site_id in header_style_mapping:
        return header_style_mapping[style_site_id].replace("[HEIGHT]", str(height))
    return pop_up_style()


def side_style(
    width: int = None,
    height: int = None,
    style_site_id: Literal["classified", "wiki", "shopping", "reddit"] = "reddit",
    scale: float = 1.0,
) -> str:
    assert width is None, "width is the sidebar size"
    assert height is None, "height is controlled by the content"
    if style_site_id in side_style_mapping:
        return side_style_mapping[style_site_id].replace("[HEIGHT]", str(height))
    return pop_up_style()


styles = {"popup": pop_up_style, "header": header_style, "side": side_style}
