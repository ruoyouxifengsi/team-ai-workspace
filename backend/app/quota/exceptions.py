class QuotaExceeded(Exception):
    def __init__(self, used: int, limit: int):
        self.used = used
        self.limit = limit
        super().__init__(f"daily token quota exceeded: {used}/{limit}")
