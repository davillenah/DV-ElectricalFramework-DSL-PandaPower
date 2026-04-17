# src/elecboard/core.py
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Literal

from .exceptions import ModelError


PhaseType = Literal["3ph", "1ph"]


@dataclass
class Element:
    tag: str


@dataclass
class Bus(Element):
    phase_type: PhaseType = "3ph"
    vn_kv_net: float = 0.38  # para pandapower
    # tensión para cálculo (p.ej. 0.22 en 1ph)
    v_calc_kv: float = 0.38


@dataclass
class Supply(Element):
    bus_tag: str
    vm_pu: float = 1.0


@dataclass
class Protection(Element):
    from_bus: str
    to_bus: str
    In_A: float
    prot_type: Literal["MCCB", "RCCB"] = "MCCB"
    # RCCB
    Idn_A: Optional[float] = None
    closed: bool = True


@dataclass
class Load(Element):
    from_bus: str
    In_A: float
    phase_type: PhaseType = "3ph"
    load_type: str = "motor"
    cos_phi: float = 0.85
    length_km: float = 0.0
    line_std_type: Optional[str] = None


@dataclass
class Project:
    frequency_hz: float = 50.0
    sn_mva: float = 1.0
    elements: Dict[str, Element] = field(default_factory=dict)
    buses: Dict[str, Bus] = field(default_factory=dict)
    supplies: List[Supply] = field(default_factory=list)
    protections: List[Protection] = field(default_factory=list)
    loads: List[Load] = field(default_factory=list)

    cursor_bus: Optional[str] = None

    def add_bus(self, bus: Bus):
        if bus.tag in self.elements:
            raise ModelError(f"Tag duplicado: {bus.tag}")
        self.elements[bus.tag] = bus
        self.buses[bus.tag] = bus
        self.cursor_bus = bus.tag

    def add_supply(self, supply: Supply):
        if supply.tag in self.elements:
            raise ModelError(f"Tag duplicado: {supply.tag}")
        self.elements[supply.tag] = supply
        self.supplies.append(supply)
        self.cursor_bus = supply.bus_tag

    def add_protection(self, prot: Protection):
        if prot.tag in self.elements:
            raise ModelError(f"Tag duplicado: {prot.tag}")
        self.elements[prot.tag] = prot
        self.protections.append(prot)
        self.cursor_bus = prot.to_bus

    def add_load(self, load: Load):
        if load.tag in self.elements:
            raise ModelError(f"Tag duplicado: {load.tag}")
        self.elements[load.tag] = load
        self.loads.append(load)
        self.cursor_bus = load.from_bus
