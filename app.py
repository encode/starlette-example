from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
import jinja2
import uvicorn


def setup_jinja2(template_dir):
    @jinja2.contextfunction
    def url_for(context, name, **path_params):
        request = context['request']
        return request.url_for(name, **path_params)

    loader = jinja2.FileSystemLoader(template_dir)
    env = jinja2.Environment(loader=loader, autoescape=True)
    env.globals['url_for'] = url_for
    return env


env = setup_jinja2('templates')
app = Starlette(debug=True)
app.mount('/static', StaticFiles(directory='statics'), name='static')


@app.route('/')
async def homepage(request):
    template = env.get_template('index.html')
    content = template.render(request=request)
    return HTMLResponse(content)


@app.route('/error')
async def error(request):
    raise RuntimeError("Oh no")


@app.exception_handler(404)
async def not_found(request, exc):
    """
    Return an HTTP 404 page.
    """
    template = env.get_template('404.html')
    content = template.render(request=request)
    return HTMLResponse(content)


@app.exception_handler(500)
async def server_error(request, exc):
    """
    Return an HTTP 500 page.
    """
    template = env.get_template('500.html')
    content = template.render(request=request)
    return HTMLResponse(content)


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)
