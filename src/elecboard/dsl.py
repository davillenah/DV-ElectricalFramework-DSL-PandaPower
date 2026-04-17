# src/elecboard/dsl.py
from __future__ import annotations

from pathlib import Path

from .config import EngineeringConfig
from .core import Project, Bus, Supply, Protection, Load
from .validators import validate_project
from .backend import build_pandapower_net
from .exceptions import ModelError


class Add:
    """
    DSL principal: Add.xxx(...)
    Se apoya en un config YAML para defaults (tensiones, frecuencia, cosφ, etc.)
    """

    _config: EngineeringConfig | None = None
    _project: Project | None = None

    # ---------------------------
    # Inicialización / Config
    # ---------------------------
    @staticmethod
    def use_config(path: str | Path) -> "Add":
        Add._config = EngineeringConfig.load(path)
        Add._project = Project(
            frequency_hz=Add._config.frequency_hz,
            sn_mva=Add._config.defaults.sn_mva
        )
        return Add

    @staticmethod
    def project() -> Project:
        if Add._project is None:
            raise ModelError("No hay proyecto inicializado. Llamá primero: Add.use_config('configs/default_ar.yaml')")
        return Add._project

    @staticmethod
    def config() -> EngineeringConfig:
        if Add._config is None:
            raise ModelError("No hay configuración cargada. Llamá primero: Add.use_config('configs/default_ar.yaml')")
        return Add._config

    # ---------------------------
    # Elementos eléctricos
    # ---------------------------
    @staticmethod
    def electricalSupply(tag: str, bus_tag: str | None = None, vm_pu: float = 1.0):
        """
        Crea una fuente y su bus asociado.
        Si bus_tag no se da, se usa el mismo tag como bus.
        """
        cfg = Add.config()
        prj = Add.project()

        btag = bus_tag or tag
        # Bus base LV
        bus = Bus(
            tag=btag,
            phase_type="3ph",
            vn_kv_net=cfg.low_voltage.vn_kv_net,
            v_calc_kv=cfg.low_voltage.vn_kv_ll
        )
        prj.add_bus(bus)

        prj.add_supply(Supply(tag=tag, bus_tag=btag, vm_pu=vm_pu))
        return Add

    @staticmethod
    def terminalBlock3PH(tag: str):
        cfg = Add.config()
        prj = Add.project()
        prj.add_bus(Bus(
            tag=tag,
            phase_type="3ph",
            vn_kv_net=cfg.low_voltage.vn_kv_net,
            v_calc_kv=cfg.low_voltage.vn_kv_ll
        ))
        return Add

    @staticmethod
    def terminalBlock1PH(tag: str):
        cfg = Add.config()
        prj = Add.project()
        # En pandapower mantenemos vn_kv_net=0.38 (base LL),
        # pero v_calc_kv=0.22 para calcular P/Q desde corriente.
        prj.add_bus(Bus(
            tag=tag,
            phase_type="1ph",
            vn_kv_net=cfg.low_voltage.vn_kv_net,
            v_calc_kv=cfg.low_voltage.vn_kv_ln
        ))
        return Add

    @staticmethod
    def mccb(tag: str, from_: str | None = None, to: str | None = None, In: float = 63.0, closed: bool = True):
        prj = Add.project()
        if from_ is None:
            from_ = prj.cursor_bus
        if from_ is None:
            raise ModelError("mccb: no se pudo inferir from_. Definí from_ explícitamente o creá un bus antes.")

        if to is None:
            raise ModelError("mccb: 'to' es obligatorio (destino).")

        prj.add_protection(Protection(
            tag=tag,
            from_bus=from_,
            to_bus=to,
            In_A=float(In),
            prot_type="MCCB",
            closed=closed
        ))
        return Add

    @staticmethod
    def rccb(tag: str, from_: str | None = None, to: str | None = None, In: float = 40.0, Idn: float | None = None, closed: bool = True):
        cfg = Add.config()
        prj = Add.project()

        if from_ is None:
            from_ = prj.cursor_bus
        if from_ is None:
            raise ModelError("rccb: no se pudo inferir from_. Definí from_ explícitamente o creá un bus antes.")

        if to is None:
            raise ModelError("rccb: 'to' es obligatorio (destino).")

        if Idn is None:
            # default típico 30 mA si no se especifica
            Idn = 0.03

        prj.add_protection(Protection(
            tag=tag,
            from_bus=from_,
            to_bus=to,
            In_A=float(In),
            prot_type="RCCB",
            Idn_A=float(Idn),
            closed=closed
        ))
        return Add

    @staticmethod
    def load(tag: str,
             In: float,
             from_: str | None = None,
             phase: str | None = None,
             load_type: str | None = None,
             cos_phi: float | None = None,
             length_km: float = 0.0,
             line_std_type: str | None = None):
        """
        Agrega una carga. Si from_ no se indica, usa el cursor_bus (último bus "activo").
        phase: "3ph" o "1ph". Si no se indica, se infiere del bus origen.
        """
        cfg = Add.config()
        prj = Add.project()

        if from_ is None:
            from_ = prj.cursor_bus
        if from_ is None:
            raise ModelError("load: no se pudo inferir from_. Definí from_ explícitamente o creá un bus antes.")

        bus = prj.buses.get(from_)
        if bus is None:
            raise ModelError(f"load: bus origen inexistente: {from_}")

        phase_type = (phase or bus.phase_type)
        lt = load_type or cfg.defaults.load_type

        if cos_phi is None:
            cos_phi = float(cfg.defaults.cos_phi.get(lt, 0.9))

        prj.add_load(Load(
            tag=tag,
            from_bus=from_,
            In_A=float(In),
            phase_type=phase_type,   # "1ph" o "3ph"
            load_type=lt,
            cos_phi=float(cos_phi),
            length_km=float(length_km),
            line_std_type=line_std_type or cfg.defaults.line_std_type
        ))
        return Add

    # ---------------------------
    # Build / Run
    # ---------------------------
    @staticmethod
    def build():
        cfg = Add.config()
        prj = Add.project()
        validate_project(prj)

        net = build_pandapower_net(prj, switch_z_ohm=float(cfg.defaults.switch_z_ohm))
        return net