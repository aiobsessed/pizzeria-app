from datetime import datetime, timezone

from fastapi.templating import Jinja2Templates

from app.core.timezone import MSK

templates = Jinja2Templates(directory="app/templates")
templates.env.filters["to_msk"] = lambda dt: dt.astimezone(MSK)
templates.env.globals["now"] = lambda: datetime.now(timezone.utc)
