"""Stage-specific public errors; never serialize the underlying exception."""


class ApplicationError(RuntimeError):
    def __init__(self, stage, error_code, next_step):
        super().__init__(next_step)
        self.stage = stage
        self.error_code = error_code
        self.next_step = next_step

    def summary(self):
        return {"status": "error", "stage": self.stage, "error_code": self.error_code,
                "next_step": self.next_step}
