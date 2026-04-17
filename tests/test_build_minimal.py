# tests/test_build_minimal.py
import pandapower as pp
from elecboard import Add

def test_build_minimal():
    Add.use_config("configs/default_ar.yaml")
    Add.electricalSupply(tag="acometida")
    Add.terminalBlock3PH(tag="x1")
    Add.mccb(tag="ig", from_="acometida", to="x1", In=100)
    Add.load(tag="l1", In=10, from_="x1", phase="3ph", load_type="motor", length_km=0.1)

    net = Add.build()
    pp.runpp(net)

    assert len(net.bus) >= 2
    assert len(net.ext_grid) == 1
    assert len(net.load) == 1