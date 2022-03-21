from mikro.app import MikroApp
from fakts import Fakts
from fakts.grants import YamlGrant


def test_app_instantiation():

    app = MikroApp(fakts=Fakts(subapp="test", grants=[YamlGrant()]))
