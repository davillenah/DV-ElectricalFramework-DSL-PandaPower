# src/elecboard/exceptions.py
class ElecboardError(Exception):
    """Excepción base del framework."""
    pass


class ConfigError(ElecboardError):
    pass


class ModelError(ElecboardError):
    pass


class ValidationError(ElecboardError):
    pass