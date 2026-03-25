# Imports #
from WiFi.Settings.wifi_settings import *


def generate_lfsr_sequence(sequence_length: int, seed: int) -> list[int]:
    r"""
    LFSR (Linear Feedback Shift Register) is a shift register whose input bit is a linear function of its previous
    state. The initial value of the LFSR is called the seed, and because the operation of the register is
    deterministic, the stream of values produced by the register is completely determined by its current (or
    previous) state. Likewise, because the register has a finite number of possible states, it must eventually enter
    a repeating cycle. The LFSR used in WiFi communications is as follows (as specified in 'Reference'):

                   -----------------------------> XOR (Feedback bit) -----------------------------------
                   |                               ^                                                   |
                   |                               |                                                   |
                   +----+      +----+      +----+  |   +----+      +----+      +----+      +----+     |
                   | X7 |<-----| X6 |<-----| X5 |<----| X4 |<-----| X3 |<-----| X2 |<-----| X1 |<-----
                   +----+      +----+      +----+      +----+      +----+      +----+      +----+

    Reference - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.5 PHY DATA scrambler and descrambler, p. 2817.

    The DATA field, composed of SERVICE, PSDU, tail, and pad parts, shall be scrambled with a length-127
    PPDU-synchronous scrambler. The octets of the PSDU are placed in the transmit serial bit stream, bit 0 first
    and bit 7 last. The PPDU synchronous scrambler is illustrated below,

                            First 7 bits of Scrambling
                            Sequence as defined in (*)
                   -------------------------------------------+
                                                               \ <---------- During bits 0-6 of Scrambling Sequence
                                                                \            when CH_BANDWIDTH_IN_NON_HT is present
                                                                 \
                                                                 |
                   +------------------------------------+        |          Data in
                   |                                             |             |
                   |                                             |             |
                   |                    +------+                 |             ↓
                   +------------------- | LFSR | <---------------+----------> XOR
                                        +------+                               |
                                                                               |
                                                                               ↓
                                                                      Scrambled data out

    (*) - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.5 PHY DATA scrambler and descrambler, Table
    17-7—Contents of the first 7 bits of the scrambling sequence, p.2818.

    :param sequence_length: Sequence length.
    :param seed: Initial 7-bit seed for LFSR (non-zero).

    :return: LFSR sequence.
    """

    # Unpack the 7-bit integer seed into individual register bits (bit 0 first).
    lfsr_state = [(seed >> i) & 1 for i in range(7)]  # 7-bit initial state.
    lfsr_sequence = []

    for _ in range(sequence_length):
        # Tap positions x^7 and x^4 per IEEE 802.11-2020 Table 17-7 scrambler polynomial.
        feedback = lfsr_state[6] ^ lfsr_state[3]  # x^7 XOR x^4.
        # append feedback bit.
        lfsr_sequence.append(feedback)
        # Shift registers.
        lfsr_state = [feedback] + lfsr_state[:-1]

    return lfsr_sequence
