from mikro.api.schema import aget_random_rep
import pytest

from mikro.app import MikroApp
from fakts import Fakts


def test_app_instantiation():

    app = MikroApp(fakts=Fakts(subapp="basic"))
