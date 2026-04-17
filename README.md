# elecboard (MVP)

Framework tipo DSL para describir tableros eléctricos (BT/MT) con sintaxis tipo:
```python
Add.electricalSupply(tag="acometida")
Add.terminalBlock3PH(tag="x1")
Add.mccb(tag="ig", from_="acometida", to="x1", In=250)
Add.terminalBlock1PH(tag="x2")
Add.rccb(tag="c1", from_="ig", to="x2")
Add.load(tag="m1", In=100, length_km=0.05, load_type="motor")
net = Add.build()
