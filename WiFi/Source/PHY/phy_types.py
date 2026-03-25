# Imports #
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class PhyVector:
    """PHY TXVECTOR / RXVECTOR: rate and frame length exchanged between MAC and PHY."""
    phy_rate: int   # PHY data rate in Mbps (6, 9, 12, 18, 24, 36, 48, or 54)
    length: int     # Number of PSDU octets


@dataclass
class MCSParameters:
    """Typed container for a single MCS (Modulation and Coding Scheme) table entry."""
    modulation: str           # e.g. 'BPSK', 'QPSK', '16-QAM', '64-QAM'
    data_coding_rate: str     # e.g. '1/2', '3/4', '2/3'
    n_bpsc: int               # Number of coded bits per subcarrier
    n_cbps: int               # Number of coded bits per OFDM symbol
    n_dbps: int               # Number of data bits per OFDM symbol
    signal_field_coding: list[int]  # 4-bit RATE field used in the SIGNAL symbol
