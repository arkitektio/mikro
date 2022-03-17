from mikro import MikroApp, get_representation
from fakts import Fakts


app = MikroApp(fakts=Fakts(subapp="basic"))
app.connect()


g = get_representation(107)
print(g)

print(g.data.max().compute())
