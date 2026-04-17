# src/elecboard/backend/pandapower_backend.py
from __future__ import annotations

import pandapower as pp

from ..core import Project, Bus
from ..utils import pq_from_current


def build_pandapower_net(project: Project, switch_z_ohm: float = 0.0):
    """
    Traduce Project -> pandapowerNet.
    - Buses: create_bus(net, vn_kv=...)  (pandapower docs) [4](https://pandapower.readthedocs.io/en/latest/elements/bus.html)
    - Fuente: create_ext_grid(net, bus=...) [3](https://www.pandapower.org/)
    - Protecciones: create_switch(net, et='b', type='CB', ...) (switch docs) [5](https://pandapower.readthedocs.io/en/v2.4.0/elements/switch.html)
    - Cargas: create_load(net, p_mw, q_mvar) [3](https://www.pandapower.org/)
    - Líneas: create_line(net, std_type=..., length_km=...) [3](https://www.pandapower.org/)
    """
    net = pp.create_empty_network(
        name="elecboard_net",
        f_hz=project.frequency_hz,
        sn_mva=project.sn_mva
    )

    bus_map: dict[str, int] = {}

    # 1) Crear buses
    for tag, bus in project.buses.items():
        assert isinstance(bus, Bus)
        bus_map[tag] = pp.create_bus(
            net,
            vn_kv=bus.vn_kv_net,
            name=tag,
            type="b"
        )

    # 2) Ext grid (fuente)
    for s in project.supplies:
        pp.create_ext_grid(
            net,
            bus=bus_map[s.bus_tag],
            vm_pu=s.vm_pu,
            name=s.tag
        )

    # 3) Protecciones (switch bus-bus)
    for prot in project.protections:
        pp.create_switch(
            net,
            bus=bus_map[prot.from_bus],
            element=bus_map[prot.to_bus],
            et="b",
            closed=prot.closed,
            type="CB",
            name=prot.tag,
            z_ohm=switch_z_ohm
        )

    # 4) Cargas (y opcional línea hasta una bornera de carga)
    for ld in project.loads:
        from_bus_pp = bus_map[ld.from_bus]
        bus_for_load = from_bus_pp

        # si hay "tramo" hasta la carga, creamos un bus local y una línea
        if ld.length_km and ld.length_km > 0:
            load_bus_tag = f"{ld.tag}__bus"
            if load_bus_tag not in bus_map:
                # heredamos vn_kv del bus upstream (BT)
                vn_kv = net.bus.loc[from_bus_pp, "vn_kv"]
                bus_map[load_bus_tag] = pp.create_bus(net, vn_kv=vn_kv, name=load_bus_tag, type="n")

            to_bus_pp = bus_map[load_bus_tag]
            std_type = ld.line_std_type or "NAYY 4x50 SE"
            pp.create_line(
                net,
                from_bus=from_bus_pp,
                to_bus=to_bus_pp,
                length_km=ld.length_km,
                std_type=std_type,
                name=f"{ld.tag}__line"
            )
            bus_for_load = to_bus_pp

        # Potencia desde corriente:
        # - 3ph usa V_ll; 1ph usa V_ln (aunque el bus esté en vn_kv_net=0.38)
        # (v_kv para cálculo debe venir desde el DSL/Config)
        # Para simplificar: si ld.phase_type=='1ph' usamos 0.22 kV asumido en ld.cos_phi/phase_type.
        # El DSL setea la tensión correcta vía v_calc_kv del bus; aquí no la tenemos, así que se calcula
        # con v_calc_kv equivalente a 0.38 (3ph) y 0.22 (1ph) si no se especifica.
        v_calc_kv = 0.38 if ld.phase_type == "3ph" else 0.22

        p_mw, q_mvar = pq_from_current(
            In_A=ld.In_A,
            v_kv=v_calc_kv,
            phase_type=ld.phase_type,
            cos_phi=ld.cos_phi
        )

        pp.create_load(
            net,
            bus=bus_for_load,
            p_mw=p_mw,
            q_mvar=q_mvar,
            name=ld.tag
        )

    return net