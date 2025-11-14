# Imports #
import copy
import random
import numpy as np
import pytest

from unittest.mock import patch
from WiFi.Source.phy import PHY, MODULATION_CODING_SCHEME_PARAMETERS, FREQUENCY_DOMAIN_STF, FREQUENCY_DOMAIN_LTF
from constants import *


@pytest.mark.parametrize("phy_rate, length",
                         [(random.choice(list(MODULATION_CODING_SCHEME_PARAMETERS.keys())), random.randint(1, 4095))
                          for _ in range(RANDOM_TESTS)])
def test_generate_signal_field(phy_rate, length):
    """
    Test purpose - Basic functionality of generating SIGNAL field based on rate and length parameters.
    Criteria - All SIGNAL field bits are generated correctly.

    Test steps:
    1) Generate random PHY rate (from a pool of possible values) and length between 1-4095 (2^12).
    2) Generate the SIGNAL field.
    3) Assert that each sub-field is bit-exact to expected outcome.
    """

    # Step (2) - Generate SIGNAL field.
    phy = PHY(identifier="")
    phy._length = length
    signal_field_coding = MODULATION_CODING_SCHEME_PARAMETERS[phy_rate]["SIGNAL_FIELD_CODING"]
    phy._signal_field_coding = signal_field_coding
    signal_field = phy.generate_signal_field()

    # Step (3) - Assert all sub-fields.
    assert signal_field[:4] == signal_field_coding                                               # Assert RATE.
    assert signal_field[4] == 0                                                                  # Assert RESERVED.
    assert signal_field[5:17] == [int(bit) for bit in format(length, '012b')][::-1]              # Assert LENGTH.
    assert signal_field[17] == 0 if np.sum(signal_field[:17]) % 2 == 0 else 1                    # Assert PARITY.
    assert signal_field[18:] == 6 * [0]                                                          # Assert SIGNAL TAIL.


@pytest.mark.parametrize(
    "sequence_length, expected_lfsr_sequence",
    [
        (127, LFSR_SEQUENCE_SEED_1011101),         # Basic sequence.
        (2 * 127, 2 * LFSR_SEQUENCE_SEED_1011101)  # Cyclic sequence.
    ]
)
def test_generate_lfsr_sequence(sequence_length, expected_lfsr_sequence):
    """
    Test purpose - Basic functionality of generating an LFSR sequence.
    Criteria:
    1) 127-bit sequence generated repeatedly is equal to a known sequence [*] when the all 1s initial state is used.
    2) Cyclic - Generated sequence cycle is 127 bits.

    Test steps:
    1) Generate LFSR sequence with seed 93.
    2) Assert that generated LFSR sequence is bit-exact to the expected value (provided by the standard).

    [*]-IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.5 PHY DATA scrambler and descrambler, p. 2817, Figure 17-7.
    """

    # Steps (1)+(2) - Generate LFSR sequence and assert it is bit-exact to the expected value.
    assert (PHY(identifier="").generate_lfsr_sequence(sequence_length=sequence_length, seed=93) ==
            expected_lfsr_sequence)


def test_bcc_encode():
    """
    Test purpose - Basic functionality of encoding using BCC.
    Criteria - Generated coded data is bit-exact to a known sequence [*].

    Test steps:
    1) Encode SIGNAL field data (taken from [**]).
    2) Assert that coded SIGNAL data is bit-exact to the expected value [*].

    [*] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.2 Coding the SIGNAL field bits, p. 4157, Table I-8—SIGNAL
    field bits after encoding.
    [**] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.1 SIGNAL field bit assignment, p. 4156, Table I-7—Bit
    assignment for SIGNAL field.
    """

    phy = PHY(identifier="")
    phy._bcc_shift_register = 7 * [0]  # Initializing the shift register.

    # Steps (1)+(2) - Encode and assert that outcome is bit-exact to expected one.
    assert phy.bcc_encode(bits=SIGNAL_FIELD, coding_rate='1/2') == ENCODED_SIGNAL_FIELD


def test_interleave():
    """
    Test purpose - Basic functionality of interleaving.
    Criteria - Generated interleaved data is bit-exact to a known sequence [*].

    Test steps:
    1) Interleave encoded SIGNAL field data (taken from [**]).
    2) Assert that interleaved coded SIGNAL data is bit-exact to the expected value [*].

    [*] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.3 Interleaving the SIGNAL field bits, p. 4157, Table
    I-9—SIGNAL field bits after interleaving.
    [**] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.2 Coding the SIGNAL field bits, p. 4157, Table I-8—SIGNAL
    field bits after encoding.
    """

    # Steps (1)+(2) - Interleave and assert that outcome is bit-exact to expected one.
    assert (PHY(identifier="").interleave(bits=ENCODED_SIGNAL_FIELD, phy_rate=6) ==
            INTERLEAVED_SIGNAL_FIELD)


def test_data_subcarrier_modulation():
    """
    Test purpose - Basic functionality of data sub-carrier modulation.
    Criteria - Generated modulated data is bit-exact to a known sequence [*].

    Test steps:
    1) Modulate interleaved SIGNAL field data (taken from [**]).
    2) Assert that modulated interleaved SIGNAL data is bit-exact to the expected value [*].

    [*] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.4 SIGNAL field frequency domain, p. 4158, Table
    I-10—Frequency domain representation of SIGNAL field.
    [**] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.3 Interleaving the SIGNAL field bits, p. 4157, Table
    I-9—SIGNAL field bits after interleaving.
    """

    # Steps (1)+(2) - Modulate interleaved SIGNAL data and assert that outcome is bit-exact to reference.
    assert (PHY(identifier="").subcarrier_modulation(bits=INTERLEAVED_SIGNAL_FIELD, phy_rate=6) ==
            MODULATED_SIGNAL_FIELD)


def test_pilot_subcarrier_insertion():
    """
    Test purpose - Basic functionality of OFDM pilot subcarrier insertion.
    Criteria - Generated OFDM symbol (frequency domain) data is bit-exact to a known sequence [*].

    Test steps:
    1) Insert pilot subcarriers into a modulated interleaved SIGNAL field data (taken from [**]).
    2) Assert that modulated SIGNAL data (with pilot sub-carriers) is bit-exact to the expected value [*].

    [*] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.4 SIGNAL field frequency domain, p. 4158-4159, Table
    I-11—Frequency domain representation of SIGNAL field with pilots inserted.
    [**] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.3 Interleaving the SIGNAL field bits, p. 4157, Table
    I-9—SIGNAL field bits after interleaving.
    """

    # Steps (1)+(2) - Modulate OFDM symbol (for SIGNAL data) and assert that outcome is bit-exact to reference.
    assert (PHY(identifier="").pilot_subcarrier_insertion(
        modulated_subcarriers=MODULATED_SIGNAL_FIELD,
        pilot_polarity=1) == FREQUENCY_DOMAIN_SIGNAL_FIELD)


@pytest.mark.parametrize(
    "ofdm_symbol, field_type, expected_value",
    [
        (FREQUENCY_DOMAIN_STF, 'STF', TIME_DOMAIN_STF),
        (FREQUENCY_DOMAIN_LTF, 'LTF', TIME_DOMAIN_LTF),
        (FREQUENCY_DOMAIN_SIGNAL_FIELD, 'SIGNAL', TIME_DOMAIN_SIGNAL_FIELD),
        # TODO: Add a test case for DATA symbol.
    ]
)
def test_convert_to_time_domain(ofdm_symbol, field_type, expected_value):
    """
    Test purpose - Basic functionality conversion to time domain which includes IFFT, addition of cyclic prefix, overlap
    sample suffix and window function.
    Criteria - Generated OFDM symbol (time domain) is bit-exact to a known sequence. The known sequences cover:
    1) STF.
    2) LTF.
    3) SIGNAL field.

    Test steps:
    1) Convert OFDM symbol to time domain.
    2) Assert that time domain OFDM symbol(s) is bit-exact to the reference value.
    """

    # Steps (1)+(2) - Convert OFDM symbol to time domain and assert it is bit-exact to the reference.
    assert PHY(identifier="").convert_to_time_domain(
        ofdm_symbol=ofdm_symbol,
        field_type=field_type) == expected_value


def test_generate_preamble():
    """
    Test purpose - Basic functionality of preamble generation.
    Criteria - Generated preamble (time domain) is bit-exact to expected outcome.

    Test steps:
    1) Generate preamble.
    2) Assert that time domain preamble is bit-exact to the expected outcome.
    """

    # Steps (1)+(2) - Generate preamble and assert it's bit-exact to expected outcome.
    assert (PHY(identifier="").generate_preamble() ==
            TIME_DOMAIN_STF[:-1] +  # STF.
            [TIME_DOMAIN_STF[-1] + TIME_DOMAIN_LTF[0]] +  # Overlap between STF and LTF.
            TIME_DOMAIN_LTF[1:])                            # LTF.


def test_generate_signal_symbol():
    """
    Test purpose - Basic functionality of SIGNAL field generation.
    Criteria - Generated SIGNAL (time domain) is bit-exact to expected outcome.

    Test steps:
    1) Generate SIGNAL.
    2) Assert that time domain SIGNAL is bit-exact to the expected outcome.
    """

    phy = PHY(identifier="")
    phy._length = 100
    phy._signal_field_coding = [1, 0, 1, 1]  # According to PHY rate = 36.
    phy._bcc_shift_register = 7 * [0]        # Initializing the shift register.

    # Steps (1)+(2) - Generate time domain SIGNAL symbol and assert it's bit-exact to expected value.
    assert phy.generate_signal_symbol() == TIME_DOMAIN_SIGNAL_FIELD


def test_generate_signal_symbol_call_count():
    """
    Test purpose - Correct call count for SIGNAL symbol generation.
    Criteria - SIGNAL generation does encoding, interleaving, modulation, pilot insertion and time domain conversion.

    Test steps:
    1) Mock all function calls to keep track of call number.
    2) Generate SIGNAL.
    3) Assert that encoding, interleaving, modulation, pilot insertion and time domain conversion occur once.
    """

    # Step (1) - Mock all relevant functions.
    with (patch.object(PHY, 'generate_signal_field') as mock_generate_signal_field,
          patch.object(PHY, 'bcc_encode') as mock_bcc_encode,
          patch.object(PHY, 'interleave') as mock_interleave,
          patch.object(PHY, 'subcarrier_modulation') as mock_subcarrier_modulation,
          patch.object(PHY, 'pilot_subcarrier_insertion') as mock_pilot_subcarrier_insertion,
          patch.object(PHY, 'convert_to_time_domain') as mock_convert_to_time_domain):

        # Step (2) - Generate time domain SIGNAL.
        PHY(identifier="").generate_signal_symbol()

        # Step (3) - Assert all relevant calls were made.
        assert mock_generate_signal_field.call_count == 1
        assert mock_bcc_encode.call_count == 1
        assert mock_interleave.call_count == 1
        assert mock_subcarrier_modulation.call_count == 1
        assert mock_pilot_subcarrier_insertion.call_count == 1
        assert mock_convert_to_time_domain.call_count == 1


def test_decode_signal():
    """
    Test purpose - PHY rate / Length decoding correctness (for the SIGNAL symbol).
    Criteria - SIGNAL decoding produces correct PHY rate and length.

    Test steps:
    1) Mock all relevant functions (to avoid block testing).
    2) Decode SIGNAL symbol and assert correct values of PHY rate and length.
    """

    # Step (1) - Mock all relevant functions.
    with (patch.object(PHY, 'convert_to_frequency_domain'),
          patch.object(PHY, 'equalize_and_remove_pilots'),
          patch.object(PHY, 'hard_decision_demapping'),
          patch.object(PHY, 'deinterleave'),
          patch.object(PHY, 'convolutional_decode_viterbi', return_value=SIGNAL_FIELD)):

        # Step (2) - Assert that parity check and PHY rate are decoded correctly.
        assert PHY(identifier="").decode_signal(signal=[]) == (36, 100)


def test_decode_signal_parity_check():
    """
    Test purpose - Parity check error case when decoding SIGNAL symbol.
    Criteria - Parity check fails when parity bit is flipped.

    Test steps:
    1) Prepare SIGNAL field with incorrect parity bit.
    2) Mock all relevant functions (to avoid block testing).
    3) Decode SIGNAL symbol and assert parity check fails.
    """

    # Step (1) - Prepare SIGNAL symbol with incorrect parity bit.
    flipped_parity_signal_field = copy.deepcopy(SIGNAL_FIELD)  # To avoid changing the SIGNAL filed for other tests.
    flipped_parity_signal_field[17] = 1 - SIGNAL_FIELD[17]     # Toggle parity bit.
    # Note - The last line logic is to avoid hard-coded flip of the bit to avoid test failure if SIGNAL filed is changed
    # in the future.

    # Step (2) - Mock all relevant functions.
    with (patch.object(PHY, 'convert_to_frequency_domain'),
          patch.object(PHY, 'equalize_and_remove_pilots'),
          patch.object(PHY, 'hard_decision_demapping'),
          patch.object(PHY, 'deinterleave'),
          patch.object(PHY, 'convolutional_decode_viterbi', return_value=flipped_parity_signal_field)):

        # Step (3) - Assert that parity check fails.
        assert PHY(identifier="").decode_signal(signal=[]) == (None, None)


def test_decode_signal_invalid_rate():
    """
    Test purpose - Invalid rate error case when decoding SIGNAL symbol.
    Criteria - Invalid rate error rises when SIGNAL symbol rate field is incorrect.

    Test steps:
    1) Prepare SIGNAL field with invalid rate field.
    2) Mock all relevant functions (to avoid block testing).
    3) Decode SIGNAL symbol and assert that relevant error rises.
    """

    # Step (1) - Prepare a SIGNAL symbol with invalid rate field.
    invalid_rate_signal_field = copy.deepcopy(SIGNAL_FIELD)  # To avoid changing the SIGNAL symbol for other tests.
    invalid_rate_signal_field[:4] = [1, 1, 1, 0]             # Toggle parity bit.

    # Step (2) - Mock all relevant functions.
    with (patch.object(PHY, 'convert_to_frequency_domain'),
          patch.object(PHY, 'equalize_and_remove_pilots'),
          patch.object(PHY, 'hard_decision_demapping'),
          patch.object(PHY, 'deinterleave'),
          patch.object(PHY, 'convolutional_decode_viterbi', return_value=invalid_rate_signal_field)):

        # Step (3) - Assert that no rate/length returns as invalid rate detected.
        assert PHY(identifier="").decode_signal(signal=[]) == (None, None)


def test_hard_decision_demapping():
    """
    Test purpose - Basic functionality of hard decision demapping.
    Criteria - Hard decision demapping of frequency domain (without pilots) SIGNAL symbol results in interleaved
    SIGNAL field.

    Test steps:
    1) Demapping of frequency domain SIGNAL symbol.
    2) Assert that result is bit-exact as interleaved SIGNAL field.
    """

    # Steps (1)+(2) - Hard decision demapping and assertion of SIGNAL symbol.
    assert PHY(identifier="").hard_decision_demapping(
        equalized_symbol=MODULATED_SIGNAL_FIELD, modulation='BPSK') == INTERLEAVED_SIGNAL_FIELD


def test_deinterleave():
    """
    Test purpose - Basic functionality of deinterleaving.
    Criteria - Deinterleave of interleaved SIGNAL symbol results in coded SIGNAL field.

    Test steps:
    1) Deinterleaving of interleaved SIGNAL symbol.
    2) Assert that result is bit-exact as coded SIGNAL field.
    """

    # Steps (1)+(2) - Deinterleaving and assertion of SIGNAL symbol.
    assert (PHY(identifier="").deinterleave(bits=INTERLEAVED_SIGNAL_FIELD, phy_rate=6) ==
            ENCODED_SIGNAL_FIELD)