# Messages

Every message the SDK produces lives in `lalafo_sdk/messages.yaml`: the description of each setting, every problem found before sending, every error. Replace any of them at runtime, for example to show form problems in Azerbaijani.

```python
from lalafo_sdk import messages

messages.use({
    "value.param_required": "{name} ({param_id}) mütləqdir",
    "value.photo_count": "1 ilə {limit} arasında şəkil lazımdır, {count} verildi",
})
```

Or from a file that holds only the keys you change:

```yaml
value:
  param_required: "{name} ({param_id}) mütləqdir"
  photo_small: "{index}. şəkil {size} baytdır, ən azı {limit} lazımdır"
error:
  captcha: lalafo uğursuz girişlərdən sonra captcha istəyir. Əvvəlcə saytda brauzerdən daxil olun.
```

```python
messages.use("messages.az.yaml")
```

Rules:

- Unknown keys raise `KeyError`.
- Keep the `{placeholders}` of the original.
- The change applies to the whole process; `messages.reset()` restores the defaults.

See every key and its text:

```python
for key, text in sorted(messages.catalog().items()):
    print(key, "=", text)
```

| Group | Used for |
| --- | --- |
| `settings.*` | Descriptions of the settings |
| `value.*` | Arguments, forms, params and photos refused before sending |
| `error.*` | Errors from lalafo and the network |

The default file: [src/lalafo_sdk/messages.yaml](https://github.com/qiyascc/lalafo-python-sdk/blob/main/src/lalafo_sdk/messages.yaml).
