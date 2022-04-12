---
sidebar_label: rath
title: fakts.rath
---

#### transpile\_np\_to\_vector

```python
@registry.register_list(
    "InputVector", lambda x, d: isinstance(x, np.ndarray) and d == 1
)
def transpile_np_to_vector(x, d)
```

Transpiles numpy vectors to InputVector

