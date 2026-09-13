from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from interfaces import Interface

BASE_DIR = Path(__file__).resolve().parent / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.proxy_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=3.0),
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
        ),
        trust_env=False,
    )

    try:
        yield
    finally:
        await app.state.proxy_client.aclose()


app = FastAPI(lifespan=lifespan)

app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), "assets")


async def proxy_api(path: str, request: Request):
    client: httpx.AsyncClient = request.app.state.proxy_client
    BACKEND_URL = request.app.state.BACKEND_URL
    url = f"{BACKEND_URL}/{path}"

    headers = dict(request.headers)
    headers.pop("host", None)

    try:
        upstream = await client.request(
            request.method,
            url,
            params=request.query_params,
            headers=headers,
            content=await request.body(),
        )
    except httpx.TimeoutException:
        raise HTTPException(504, "Backend timeout")
    except httpx.RequestError as error:
        raise HTTPException(502, f"Backend unavailable: {error}")

    result = Response(
        content=upstream.content,
        status_code=upstream.status_code,
    )

    excluded = {
        "content-length",
        "transfer-encoding",
        "connection",
        "content-encoding",
    }

    for name, value in upstream.headers.multi_items():
        if name.lower() in excluded:
            continue

        if name.lower() == "set-cookie":
            result.headers.append("set-cookie", value)
        else:
            result.headers[name] = value

    return result


@app.get("/{path:path}")
async def pages(path: str):
    return FileResponse(BASE_DIR / "index.html")


class WebUi(Interface):
    ID = "web-ui"

    async def start(self):
        port = int(self.config.get("port", 3000))
        host = self.config.get("host", "0.0.0.0")
        app.state.BACKEND_URL = self.config.get("backend_url", "http://127.0.0.1:8000")
        if self.config.get("use_internal_proxy", True):
            app.add_api_route(
                "/api/{path:path}",
                proxy_api,
                methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            )
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r".*",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        config = uvicorn.Config(app, port=port, host=host)
        server = uvicorn.Server(config)
        await server.serve()
