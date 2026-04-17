# examples/ejemplo_tablero_bt.py
import pandapower as pp
from elecboard import Add

# Carga config AR (380/220 V - 50 Hz)
Add.use_config("configs/default_ar.yaml")

# DSL estilo tablero
Add.electricalSupply(tag="red", bus_tag="acometida")
Add.terminalBlock3PH(tag="x1")
Add.mccb(tag="ig", from_="acometida", to="x1", In=250)

Add.terminalBlock1PH(tag="x2")
Add.rccb(tag="c1", from_="x1", to="x2", In=40, Idn=0.03)

# Carga monofásica (ejemplo), tramo de cable 50 m
Add.load(tag="m1", In=16, from_="x2", phase="1ph", load_type="resistive", length_km=0.05)

net = Add.build()

# Correr flujo de carga
pp.runpp(net)

print("Resultados de tensión (pu):")
print(net.res_bus[["vm_pu"]])

print("\nCargas (%):")
print(net.res_line[["loading_percent"]] if len(net.line) else "Sin líneas")