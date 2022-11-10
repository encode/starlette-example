from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.routing import Route, Mount
from starlette.templating import Jinja2Templates
import uvicorn


templates = Jinja2Templates(directory='templates')


async def homepage(request):
    template = "index.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context)


async def error(request):
    """
    An example error. Switch the `debug` setting to see either tracebacks or 500 pages.
    """
    raise RuntimeError("Oh no")


async def not_found(request: Request, exc: HTTPException):
    """
    Return an HTTP 404 page.
    """
    template = "404.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context, status_code=404)


async def server_error(request: Request, exc: HTTPException):
    """
    Return an HTTP 500 page.
    """
    template = "500.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context, status_code=500)

routes = [
    Route('/', homepage),
    Route('/error', error),
    Mount('/static', app=StaticFiles(directory='statics'), name='static')
]

exception_handlers = {
    404: not_found,
    500: server_error
}

app = Starlette(debug=True, routes=routes, exception_handlers=exception_handlers)


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)
    