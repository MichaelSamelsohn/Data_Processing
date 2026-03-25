# Imports #
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class FrameParameters:
    """Typed container for MAC frame construction parameters."""
    type: str
    destination_address: list[int]
    wait_for_confirmation: bool | str = False  # False, "ACK", or "CTS"
    direction: str = ""                        # "Uplink", "Downlink", or "" for mgmt/ctrl
    retry: int = 0                             # 0 = original frame, 1 = retransmission


@dataclass
class FrameStatistic:
    """Single frame exchange record stored in MAC._statistics."""
    direction: str                                           # "TX" or "RX"
    type: str                                               # Frame type string, e.g. "Beacon", "ACK"
    source_address: list[int] = field(default_factory=list)
    destination_address: list[int] = field(default_factory=list)
    frame_size: int | None = None        # PSDU size in bytes
    phy_rate: int | None = None          # PHY rate in Mbps
    retry_attempts: int | None = None    # None = no retry tracking; 0+ = attempt count
    confirmed: bool | None = None        # True = ACK/CTS received; False = dropped; None = N/A
