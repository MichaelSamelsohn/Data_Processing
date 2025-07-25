"""
Script Name - wifi.py

TODO: Add explanation as to what this script does.

Created by Michael Samelsohn, 19/07/25.
"""

# Imports #
from Settings.settings import log


def lfsr(sequence_length: int, seed=127) -> list[int]:
    """
    LFSR (Linear Feedback Shift Register) is a shift register whose input bit is a linear function of its previous
    state. The initial value of the LFSR is called the seed, and because the operation of the register is deterministic,
    the stream of values produced by the register is completely determined by its current (or previous) state. Likewise,
    because the register has a finite number of possible states, it must eventually enter a repeating cycle.
    The LFSR used in WiFi communications is as follows (as specified in [*]):

                   -----------------------------> XOR (Feedback bit) -----------------------------------
                   |                               ^                                                   |
                   |                               |                                                   |
                +----+      +----+      +----+     |    +----+      +----+      +----+      +----+     |
                | X7 |<-----| X6 |<-----| X5 |<---------| X4 |<-----| X3 |<-----| X2 |<-----| X1 |<-----
                +----+      +----+      +----+          +----+      +----+      +----+      +----+

    [*] - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.5 PHY DATA scrambler and descrambler, p. 2817.

    :param sequence_length: Sequence length.
    :param seed: Initial 7-bit seed for LFSR (non-zero).

    :return: Scrambling sequence.
    """

    lfsr_state = [(seed >> i) & 1 for i in range(7)]  # 7-bit initial state.
    log.debug(f"LFSR initialized with seed {seed} - {lfsr_state[::-1]}")
    lfsr_sequence = []

    for i in range(sequence_length):
        # Calculate the feedback bit.
        feedback = lfsr_state[6] ^ lfsr_state[3]  # x^7 XOR x^4.
        # append feedback bit.
        lfsr_sequence.append(feedback)
        # Shift registers.
        lfsr_state = [feedback] + lfsr_state[:-1]

    return lfsr_sequence


def scramble(data_bits: list[int]) -> list[int]:
    """
    TODO: Complete the docstring.
    """

    lfsr_sequence = lfsr(sequence_length=len(data_bits))
    return [a ^ b for a, b in zip(lfsr_sequence, data_bits)]

