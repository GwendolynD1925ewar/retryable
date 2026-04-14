import pytest
from unittest.mock import MagicMock, patch
from retryable.core import retry


def test_succeeds_on_first_attempt():
    mock_fn = MagicMock(return_value="ok")

    @retry(max_attempts=3)
    def fn():
        return mock_fn()

    assert fn() == "ok"
    assert mock_fn.call_count == 1


def test_retries_on_failure_then_succeeds():
    mock_fn = MagicMock(side_effect=[ValueError("fail"), ValueError("fail"), "ok"])

    @retry(max_attempts=3, exceptions=ValueError, base_delay=0, jitter=False)
    def fn():
        return mock_fn()

    assert fn() == "ok"
    assert mock_fn.call_count == 3


def test_raises_after_max_attempts():
    mock_fn = MagicMock(side_effect=ValueError("always fails"))

    @retry(max_attempts=3, exceptions=ValueError, base_delay=0, jitter=False)
    def fn():
        return mock_fn()

    with pytest.raises(ValueError, match="always fails"):
        fn()

    assert mock_fn.call_count == 3


def test_does_not_retry_unspecified_exception():
    @retry(max_attempts=3, exceptions=ValueError, base_delay=0, jitter=False)
    def fn():
        raise TypeError("not retried")

    with pytest.raises(TypeError, match="not retried"):
        fn()


def test_on_retry_callback_is_called():
    on_retry = MagicMock()
    mock_fn = MagicMock(side_effect=[RuntimeError("boom"), "ok"])

    @retry(max_attempts=2, exceptions=RuntimeError, base_delay=0, jitter=False, on_retry=on_retry)
    def fn():
        return mock_fn()

    fn()
    on_retry.assert_called_once()
    args = on_retry.call_args[0]
    assert args[0] == 1
    assert isinstance(args[1], RuntimeError)


def test_jitter_applies_random_delay():
    with patch("retryable.core.time.sleep") as mock_sleep, \
         patch("retryable.core.random.uniform", return_value=0.42) as mock_uniform:
        mock_fn = MagicMock(side_effect=[ValueError("x"), "ok"])

        @retry(max_attempts=2, exceptions=ValueError, base_delay=1.0, jitter=True)
        def fn():
            return mock_fn()

        fn()
        mock_uniform.assert_called_once()
        mock_sleep.assert_called_once_with(0.42)


def test_invalid_max_attempts_raises():
    with pytest.raises(ValueError, match="max_attempts"):
        retry(max_attempts=0)


def test_invalid_delays_raise():
    with pytest.raises(ValueError, match="base_delay"):
        retry(base_delay=-1)

    with pytest.raises(ValueError, match="max_delay"):
        retry(base_delay=10, max_delay=5)
