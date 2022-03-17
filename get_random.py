from mikro.api.schema import get_random_rep, get_representation
from mikro import MikroApp
from fakts import Fakts


app = MikroApp(fakts=Fakts(subapp="basic"))
app.connect()


g = get_representation(107)
print(g)

print(g.data.max().compute())
