class SummarizationError(Exception):
    pass


class ValidationError(SummarizationError):
    pass


class TextTooShortError(ValidationError):
    pass


class TextTooLongError(ValidationError):
    pass
