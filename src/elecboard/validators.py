# src/elecboard/validators.py
from .exceptions import ValidationError
from .core import Project


def validate_project(project: Project):
    # Frecuencia local por defecto (AR): 50 Hz
    if abs(project.frequency_hz - 50.0) > 1e-6:
        # permitimos, pero avisamos con excepción suave si quisieras
        pass

    # Validar referencias a buses
    for s in project.supplies:
        if s.bus_tag not in project.buses:
            raise ValidationError(f"Supply {s.tag} referencia bus inexistente: {s.bus_tag}")

    for p in project.protections:
        if p.from_bus not in project.buses:
            raise ValidationError(f"Protección {p.tag} from_bus inexistente: {p.from_bus}")
        if p.to_bus not in project.buses:
            raise ValidationError(f"Protección {p.tag} to_bus inexistente: {p.to_bus}")

    for ld in project.loads:
        if ld.from_bus not in project.buses:
            raise ValidationError(f"Carga {ld.tag} from_bus inexistente: {ld.from_bus}")

    # Al menos una supply
    if not project.supplies:
        raise ValidationError("El proyecto no tiene fuente (electricalSupply).")