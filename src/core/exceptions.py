class AppError(Exception):
    pass


class DomainError(AppError):
    pass


class InfraError(AppError):
    pass


class WebhookSignatureError(AppError):
    def __init__(self, message: str = 'Invalid webhook signature') -> None:
        super().__init__(message)
        self.status_code = 403
