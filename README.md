# retryable

A Python decorator library for configurable retry logic with exponential backoff and jitter support.

---

## Installation

```bash
pip install retryable
```

---

## Usage

```python
from retryable import retry

@retry(max_attempts=5, backoff=2.0, jitter=True)
def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

The decorator will automatically retry `fetch_data` on failure, waiting progressively longer between each attempt. You can customize the behavior with the following parameters:

| Parameter | Default | Description |
|---|---|---|
| `max_attempts` | `3` | Maximum number of retry attempts |
| `backoff` | `1.5` | Exponential backoff multiplier |
| `jitter` | `False` | Add random jitter to delay intervals |
| `exceptions` | `Exception` | Exception types that trigger a retry |
| `delay` | `1.0` | Initial delay in seconds |

```python
from retryable import retry
import requests

@retry(max_attempts=3, delay=0.5, exceptions=(requests.Timeout, requests.ConnectionError))
def call_api():
    return requests.get("https://api.example.com/data", timeout=5)
```

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/yourname/retryable).

---

## License

This project is licensed under the [MIT License](LICENSE).