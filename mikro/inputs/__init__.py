"""Builders for the generated inputs that are tedious to spell out by hand.

Nothing is re-exported here on purpose: :mod:`mikro.inputs.render` and :mod:`mikro.inputs.picker`
import the generated schema at module level, and pulling that into every ``import mikro`` is the
cost the root avoids. Reach for ``from mikro.inputs.render import ...``.
"""
