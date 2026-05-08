class NotFoundError(ValueError):
    pass


class ConflictError(ValueError):
    pass


class BusinessError(ValueError):
    pass


class AuthError(ValueError):
    pass


class FrontendRedirect(Exception):
    """Поднимается frontend-зависимостями для перенаправления неавторизованных запросов.
    Обработчик в main.py: для HTMX-запросов → 401, иначе → 302 редирект.
    """

    def __init__(self, url: str) -> None:
        self.url = url
