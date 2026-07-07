# app/core/exceptions.py
class XENOError(Exception):
    """Base XENO exception."""
    pass

class ModelNotFoundError(XENOError):
    pass

class OllamaConnectionError(XENOError):
    pass

class ToolExecutionError(XENOError):
    pass