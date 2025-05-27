import asyncio
from contextlib import asynccontextmanager, suppress
import inspect
import logging
import os
from typing import Literal, Optional
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pycdp import cdp
from pycdp.asyncio import connect_cdp
from ad import get_ad_html, CLICK_SCRIPT
from styles import styles
from enhance import enhance_prompt


SERVER_ADDR = "0.0.0.0"
AD_SERVER_PORT = int(os.getenv("AD_SERVER_PORT", 61234))
CDP_PORT = 9222 + int(os.getenv("PORT_SHIFT", 0))
print(f"CDP_PORT: {CDP_PORT}")

logger = logging.getLogger("server")
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(f"result_{os.getenv('PORT_SHIFT', 0)}.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s, %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


async def attack(target_cdp_url=f"http://localhost:{CDP_PORT}"):
    print("Injecting ad: ")
    conn = (
        state["conn"] if "conn" in state else await connect_cdp(target_cdp_url)
    )
    state["conn"] = conn
    targets = await conn.execute(cdp.target.get_targets())
    for target in targets:
        try:
            if target.type_ != "page":
                continue
            if target.target_id in state["known_targets"]:
                continue

            print(f"Attacking target {target.target_id}")
            state["known_targets"].append(target.target_id)

            target_session = await conn.connect_session(target.target_id)
            await target_session.execute(cdp.page.enable())
            await target_session.execute(cdp.page.set_bypass_csp(True))
            await target_session.execute(
                cdp.security.set_ignore_certificate_errors(ignore=True)
            )
            await target_session.execute(cdp.security.disable())
            await target_session.execute(
                cdp.page.add_script_to_evaluate_on_new_document(
                    source=state["injection_content"]
                )
            )
            await target_session.execute(cdp.page.reload())
        except Exception as target_exception:
            print(
                f"Error processing target {target.target_id}: {target_exception}"
            )
            continue


async def remove_ad():
    print("Removing ad: ")
    if "conn" in state:
        with suppress(Exception):
            await state["conn"].close()
        state.pop("conn")
    state["known_targets"] = []


async def daemon():
    while True:
        try:
            if state["cdp_injection"]:
                await attack()
            else:
                await remove_ad()
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error {repr(e)}, reseting ad server.")
            await remove_ad()
            state["cdp_injection"] = False
            await asyncio.sleep(1)



@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(daemon())
    yield


state = {"cdp_injection": False, "known_targets": []}

app = FastAPI(lifespan=lifespan)

app.mount("/ad/assets", StaticFiles(directory="assets"), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/step")
async def step():
    if "step" in state:
        state["step"] += 1

@app.get("/tag")
async def tag(tag: str):
    logger.info(f"{tag}")

# In order to enhance concealment, use close_ad instead of stop_cdp_injection.
@app.get("/close_ad")
async def stop_cdp_injection(finished: Optional[bool] = False):
    await asyncio.sleep(2)
    if not finished and "tag" in state:
        logger.info(f"{state['tag']}, clicked, {state['step']}")
    if finished:
        if "tag" not in state:
            state["tag"] = "unknown"
        if "step" not in state:
            state["step"] = "unknown"
        if state["cdp_injection"]:
            logger.info(f"{state['tag']}, failed, {state['step']}")
        state.pop("tag")
        state.pop("step")
    state["cdp_injection"] = False


@app.get("/start_cdp_injection/{tag}/{ad_id}")
async def start_cdp_injection(
    request: Request,
    ad_id: str,
    tag: str,
    style: Optional[str] = "popup",
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
    enhance: Optional[str] = None,
):

    signature = inspect.signature(start_cdp_injection)
    explicit_params = [
        param_name
        for param_name, _ in signature.parameters.items()
        if param_name != "request"
    ]
    query_params = dict(request.query_params)
    extra_params_for_style = {
        key: value for key, value in query_params.items() if key not in explicit_params
    }

    extra_content = ""
    if enhance is not None and "style_site_id" in extra_params_for_style:
        extra_content = enhance_prompt(extra_params_for_style["style_site_id"])

    ad_html = await get_ad_html(
        ad_id=ad_id,
        link=link if link else f"http://{SERVER_ADDR}:{AD_SERVER_PORT}/close_ad",
        site=site,
        title=title,
        subtitle=subtitle,
        content=content + extra_content,
        btntext=btntext,
        imgalt=imgalt,
        imgpath=imgpath,
        server=server if server else SERVER_ADDR,
        port=port if port else str(AD_SERVER_PORT),
    )

    style_func = styles.get(style, None)
    if not style_func:
        raise HTTPException(status_code=404, detail="Style not found")
    state["injection_content"] = (
        style_func(**extra_params_for_style).replace("[HTML]", ad_html) + CLICK_SCRIPT
    )
    # print(state["injection_content"])
    state["tag"] = tag
    state["step"] = 0
    state["cdp_injection"] = True


if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_ADDR, port=AD_SERVER_PORT)
