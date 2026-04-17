# src/elecboard/config.py
from dataclasses import dataclass
from pathlib import Path
import yaml

from .exceptions import ConfigError


@dataclass(frozen=True)
class LVConfig:
    vn_kv_net: float
    vn_kv_ll: float
    vn_kv_ln: float


@dataclass(frozen=True)
class DefaultsConfig:
    sn_mva: float
    cos_phi: dict
    load_type: str
    line_std_type: str
    switch_z_ohm: float


@dataclass(frozen=True)
class EngineeringConfig:
    country: str
    frequency_hz: float
    low_voltage: LVConfig
    defaults: DefaultsConfig
    aea_limits: dict

    @staticmethod
    def load(path: str | Path) -> "EngineeringConfig":
        p = Path(path)
        if not p.exists():
            raise ConfigError(f"No se encontró el archivo de configuración: {p}")

        with p.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        try:
            lv = LVConfig(**raw["low_voltage"])
            d = DefaultsConfig(**raw["defaults"])
            return EngineeringConfig(
                country=raw.get("country", "AR"),
                frequency_hz=float(raw.get("frequency_hz", 50.0)),
                low_voltage=lv,
                defaults=d,
                aea_limits=raw.get("aea_limits", {}),
            )
        except Exception as e:
            raise ConfigError(f"Config inválida: {e}") from e
