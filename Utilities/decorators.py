# Imports #
import time
from Settings.settings import log


def measure_runtime(func):
    def inner(*args, **kwargs):
        log.debug(f"Beginning time measurement for method - {func.__name__}")
        start_time = time.time()
        result = func(*args, **kwargs)
        log.info(f"The runtime of the function, {func.__name__}, is - {round(time.time() - start_time, 3)} seconds")
        return result
    return inner


def log_suppression(level):
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
