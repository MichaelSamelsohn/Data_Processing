# Imports #
import time

from Image_Processing.Settings.image_settings import log


def measure_runtime(func):
    def inner(*args, **kwargs):
        log.debug(f"Beginning time measurement for method - {func.__name__}")
        start_time = time.time()
        result = func(*args, **kwargs)
        log.info(f"The runtime of the function, {func.__name__}, is - {round(time.time() - start_time, 3)} seconds")
        return result
    return inner


def log_suppression(level):
    # Temporarily raise the logger's minimum level to `level` so the decorated function's internal logs are hidden.
    def wrapper(func):
        def inner(*args, **kwargs):
            # Remembering the current log level.
            current_log_level = log.log_level
            # Suppressing the log.
            log.log_level = level
            result = func(*args, **kwargs)
            # Un-suppressing the log.
            log.log_level = current_log_level
            return result
        return inner
    return wrapper


def book_reference(book, reference):
    def wrapper(func):
        def inner(*args, **kwargs):
            log.info(f"The following method is referenced from the book - {book}")
            log.info(f"Reference for the implementation - {reference}")
            return func(*args, **kwargs)
        return inner
    return wrapper


def article_reference(article):
    def wrapper(func):
        def inner(*args, **kwargs):
            log.info(f"The following method is referenced from the article - {article}")
            return func(*args, **kwargs)
        return inner
    return wrapper


_RETRY_SENTINEL = object()  # Unique sentinel distinguishing "no default supplied" from None.


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 1.0,
          exceptions: tuple = (Exception,), default=_RETRY_SENTINEL):
    """
    Retry a function when it raises one of the specified exceptions.

    Each failed attempt is logged as a warning; the final failure is logged as an error.
    Between attempts the decorator sleeps for ``delay`` seconds; after each retry the wait
    is multiplied by ``backoff`` (set ``backoff=2.0`` for exponential back-off, leave at
    ``1.0`` for a constant interval)::

        @retry(max_attempts=3, delay=5.0,
               exceptions=(requests.exceptions.Timeout,
                            requests.exceptions.ConnectionError),
               default=None)
        def get_request(url: str) -> dict | None:
            response = requests.get(url, timeout=30)
            ...

    :param max_attempts: Total number of calls including the first attempt. Default 3.
    :param delay:        Seconds to wait before the first retry. Default 1.0.
    :param backoff:      Multiplier applied to ``delay`` after each failure. Default 1.0.
    :param exceptions:   Exception types that trigger a retry. Default ``(Exception,)``.
    :param default:      Value returned when all attempts fail.  If omitted the last
                         exception is re-raised.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            wait = delay
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        log.warning(
                            f"[{func.__name__}] Attempt {attempt}/{max_attempts} failed "
                            f"({type(exc).__name__}: {exc}). Retrying in {wait:.1f}s")
                        time.sleep(wait)
                        wait *= backoff
                    else:
                        log.error(
                            f"[{func.__name__}] All {max_attempts} attempts failed. "
                            f"Last error: {exc}")
            if default is not _RETRY_SENTINEL:
                return default
            raise last_exc
        return wrapper
    return decorator
