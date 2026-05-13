from zoneinfo import ZoneInfo

from fastapi.templating import Jinja2Templates

_MSK = ZoneInfo("Europe/Moscow")

templates = Jinja2Templates(directory="app/templates")
templates.env.filters["to_msk"] = lambda dt: dt.astimezone(_MSK)
