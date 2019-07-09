# import databases
# import sqlalchemy
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates


templates = Jinja2Templates(directory='templates')
statics = StaticFiles(directory='statics')
# database = databases.Database("sqlite:///db.sqlite")
# metadata = sqlalchemy.MetaData()
