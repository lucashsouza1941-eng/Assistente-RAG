class AppError(Exception):
    pass


class DomainError(AppError):
    pass


class InfraError(AppError):
    pass


class WebhookSignatureError(AppError):
    pass
