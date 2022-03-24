import numpy as np
from mikro import MikroApp
from fakts import Fakts
from mikro.api.schema import create_roi, RoiTypeInput
from rich.traceback import install

install()

app = MikroApp(fakts=Fakts(subapp="basic"))

with app:

    roi = create_roi(
        105, type=RoiTypeInput.LINE, vectors=np.array([[1, 3, 7], [1, 6, 5]]), creator=2
    )

    print(roi.vector_data)
