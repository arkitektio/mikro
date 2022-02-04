from pydantic import BaseModel
from mikro.mikro import Mikro
from mikro.mikro import get_current_mikro
from rath.turms.operation import GraphQLOperation

class GraphQLMikroOperation(GraphQLOperation):

    @classmethod
    def execute(cls, variables, mikro: Mikro = None):
        mikro = mikro or get_current_mikro()
        return cls(**mikro.execute(cls.get_meta().document, variables).data)

    @classmethod
    async def aexecute(cls, variables, mikro: Mikro = None):
        mikro = mikro or get_current_mikro()
        return cls(**(await mikro.aexecute(cls.get_meta().document, variables)).data)

    class Meta:
        abstract = True


class GraphQLQuery(GraphQLMikroOperation):
    class Meta:
        abstract = True


class GraphQLMutation(GraphQLMikroOperation):
    class Meta:
        abstract = True


class GraphQLSubscription(GraphQLMikroOperation):
    class Meta:
        abstract = True