# src/elecboard/utils.py
import math

def pq_from_current(In_A: float, v_kv: float, phase_type: str, cos_phi: float):
    """
    Calcula P y Q (MW, MVAr) desde corriente y tensión.
    - 3ph: P = sqrt(3) * V_ll * I * cosφ
    - 1ph: P = V_ln * I * cosφ
    v_kv se interpreta en kV.
    """
    V = v_kv * 1000.0  # V
    I = In_A
    cosphi = max(0.01, min(1.0, cos_phi))
    phi = math.acos(cosphi)
    tanphi = math.tan(phi)

    if phase_type == "3ph":
        P_w = math.sqrt(3) * V * I * cosphi
    else:
        P_w = V * I * cosphi

    Q_var = (P_w * tanphi)

    return P_w / 1e6, Q_var / 1e6  # MW, MVAr