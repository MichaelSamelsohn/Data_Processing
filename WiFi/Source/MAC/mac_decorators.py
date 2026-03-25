# Imports #
import functools

from WiFi.Source.MAC.mac_types import FrameStatistic


def role_guard(role: str, cast: str = None):
    """
    Return early from a handler if this device's role or the frame's cast type doesn't match.

    :param role: Required device role — "AP" or "STA".
    :param cast: Required cast type — "Unicast", "Broadcast", or None to skip the cast check.
    """
    required_cast = cast
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, source_address, cast):
            if self._role != role or (required_cast is not None and cast != required_cast):
                return
            return func(self, source_address, cast)
        return wrapper
    return decorator


def record_rx_stat(frame_type: str):
    """
    Prepend a FrameStatistic RX entry to self._statistics before the handler body runs.

    :param frame_type: Human-readable frame type string stored in the statistic record.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, source_address, cast):
            self._statistics.append(FrameStatistic(
                direction="RX", type=frame_type, source_address=source_address))
            return func(self, source_address, cast)
        return wrapper
    return decorator


def send_ack(func):
    """Send an ACK frame to source_address before the handler body runs."""
    @functools.wraps(func)
    def wrapper(self, source_address, cast):
        self.send_acknowledgement_frame(source_address=source_address)
        return func(self, source_address, cast)
    return wrapper
