class TariffNotFound(Exception):
    pass


class PaymentNotFound(Exception):
    pass


class InvalidTransition(Exception):
    def __init__(self, current: str, requested: str) -> None:
        self.current = current
        self.requested = requested
        super().__init__(f"{current} -> {requested}")
