# Imports #
import time
from unittest.mock import patch
import pytest
from WiFi.Source.chip import CHIP
from channel import Channel
from constants import *


@pytest.mark.parametrize(
    "authentication_algorithm", ["open-system", "shared-key"]
)
def test_basic_association(authentication_algorithm):
    """
    Test purpose - Basic functionality of authentication and association between AP and STA.
    Criteria - Connected AP and STA authenticate and associate in a given timeframe.

    Test steps:
    1) Set the channel, AP and STA. The STA is configured with an authentication algorithm.
    2) Set a timeframe for the AP and STA to authenticate and associate.
    3) Assert that both sides authenticated and associated.
    4) Shutdown (to avoid unnecessary data leaks to next tests).
    """

    # Step (1) - Set AP, STA and channel.
    channel = Channel(channel_response=[1], snr_db=25)
    ap = CHIP(role='AP', identifier="AP")
    sta = CHIP(role='STA', identifier="STA 1")
    sta.mac.authentication_algorithm = authentication_algorithm

    # Step (2) - Buffer time to allow for the association to happen.
    time.sleep(60)

    # Step (3) - Check that AP and STA are authenticated and associated (both sides).
    try:
        assert len(ap.mac._associated_sta) == 1,                  "AP is not associated with STA"
        assert ap.mac._associated_sta[0] == sta.mac._mac_address, "AP is not associated with STA"
        assert sta.mac._associated_ap == ap.mac._mac_address,     "STA is not associated with AP"

    # Step (4) - Shutdown.
    finally:
        ap.shutdown()
        sta.shutdown()
        channel.shutdown()


def test_failed_authentication_incorrect_wep_keys():
    """
    Test purpose - Failed authentication when different WEP keys are used for AP/STA.
    Criteria - AP is blacklisted for STA after several failed authentication attempts.

    Test steps:
    1) Set the channel, AP and STA. Swap the STA WEP keys.
    2) Set a timeframe for the AP and STA to fail authentication multiple times.
    3) Assert that both sides are not authenticated and AP is blacklisted for the STA.
    4) Shutdown (to avoid unnecessary data leaks to next tests).
    """

    # Step (1) - Set AP, STA and channel. The STA WEP keys are swapped.
    channel = Channel(channel_response=[1], snr_db=25)
    ap = CHIP(role='AP', identifier="AP")
    sta = CHIP(role='STA', identifier="STA 1")
    sta.mac.authentication_algorithm = "shared-key"
    sta.mac.wep_keys[0], sta.mac.wep_keys[1] = sta.mac.wep_keys[1], sta.mac.wep_keys[0]

    # Step (2) - Buffer time to allow for several authentication failures to happen.
    time.sleep(120)

    # Step (3) - Check that AP and STA are not authenticated (both sides) and AP is blacklisted for STA.
    try:
        assert len(ap.mac._authenticated_sta) == 0, "AP is authenticated with STA, although it shouldn't be"
        assert sta.mac._associated_ap is None,      "STA is authenticated with AP, although it shouldn't be"
        assert ap.mac._mac_address in sta.mac._probed_ap_blacklist, "AP is not blacklisted for STA"

    # Step (4) - Shutdown.
    finally:
        ap.shutdown()
        sta.shutdown()
        channel.shutdown()


def test_send_data_with_association():
    """
    Test purpose - Basic functionality of data sending from AP and STA (DL) when associated.
    Criteria - STA stores data received from AP in a given timeframe.

    Test steps:
    1) Set the channel, AP and STA with patched advertisement functionality.
    2) Mock association between AP and STA.
    3) Send data from AP to STA (DL).
    4) Set a timeframe for the STA to receive and decipher the data.
    5) Assert that the message was received correctly on the STA side.
    6) Shutdown (to avoid unnecessary data leaks to next tests).
    """

    # Step (1) - Setting channel, AP and STA (with patched advertisement functionality).
    channel = Channel(channel_response=[1], snr_db=25)
    with (patch('chip.MAC.beacon_broadcast', return_value=None),
          patch('chip.MAC.scanning', return_value=None)):
        # Setting the AP and STA.
        ap = CHIP(role='AP', identifier="AP")
        sta = CHIP(role='STA', identifier="STA 1")

        # Step (2) - Mocking association between AP and STA.
        ap.mac._associated_sta = [sta.mac._mac_address]
        sta.mac._associated_ap = ap.mac._mac_address

        # Step (3) - Sending the data message from AP to STA (DL).
        ap.send_text(text=MESSAGE)

        # Step (4) - Buffer time to allow for the data to be sent and received.
        time.sleep(15)

        # Step (5) - Asserting that the message was received successfully.
        try:
            assert sta.mac._last_data.decode('utf-8') == MESSAGE, "Received message is not the same as original one"

        # Step (6) - Shutdown.
        finally:
            ap.shutdown()
            sta.shutdown()
            channel.shutdown()


def test_send_data_without_association():
    """
    Test purpose - STA doesn't accept data frames from an unassociated AP.
    Criteria - STA discards frames received from an unassociated AP.

    Test steps:
    1) Set the channel, AP and STA with patched advertisement functionality.
    2) Send data from AP to STA (DL).
    3) Set a timeframe for the STA to receive and discard the frame several times (retry mechanism).
    4) Assert that the message is not received on the STA side.
    5) Shutdown (to avoid unnecessary data leaks to next tests).
    """

    # Step (1) - Setting channel, AP and STA (with patched advertisement functionality).
    channel = Channel(channel_response=[1], snr_db=25)
    with (patch('chip.MAC.beacon_broadcast', return_value=None),
          patch('chip.MAC.scanning', return_value=None)):
        ap = CHIP(role='AP', identifier="AP")
        sta = CHIP(role='STA', identifier="STA 1")
        # Mocking association between AP and STA (AP side only).
        ap.mac._associated_sta = [sta.mac._mac_address]

        # Step (2) - Sending the data message from AP to STA (DL).
        ap.send_text(text=MESSAGE)

        # Step (3) - Buffer time to allow for the data to be sent and received.
        time.sleep(60)

        # Step (4) - Asserting that the message was discarded at all times.
        try:
            assert sta.mac._last_data is None, "Data was sent without association"

        # Step (5) - Shutdown.
        finally:
            ap.shutdown()
            sta.shutdown()
            channel.shutdown()


def test_fixed_rate_configuration():
    """
    Test purpose - Basic functionality of setting a fixed/non-fixed rate.
    Criteria - Fixed rate device doesn't use rate selection. Non fixed rate devices changes rate dynamically.

    Test steps:
    1) Set the channel, AP (with fixed rate) and STA (without fixed rate).
    2) Set a timeframe for the STA to change its rate.
    3) Assert that AP remains with same initial rate and STA has different rates.
    4) Shutdown (to avoid unnecessary data leaks to next tests).
    """

    # Step (1) - Set AP (with fixed rate), STA (without fixed rate) and channel.
    channel = Channel(channel_response=[1], snr_db=25)
    ap = CHIP(role='AP', identifier="AP")
    ap.mac.phy_rate = 6
    ap.mac.is_fixed_rate = True
    is_ap_rate_fixed = True
    sta = CHIP(role='STA', identifier="STA 1")
    sta.mac.phy_rate = 6
    sta.mac.is_fixed_rate = False
    is_sta_rate_not_fixed = False

    # Step (2) - Set a timeframe for the STA to change its rate.
    try:
        for _ in range(60):
            # Raise relevant flags.
            if not ap.mac.phy_rate == 6:
                is_ap_rate_fixed = False
            if not sta.mac.phy_rate == 6:
                is_sta_rate_not_fixed = True

            # Buffer time between consecutive checks.
            time.sleep(1)

        # Step (3) - Assert that AP remains with same initial rate and STA has different rates.
        if not is_ap_rate_fixed and is_sta_rate_not_fixed:
            assert False, "AP rate is not fixed, although it should be"
        elif is_ap_rate_fixed and not is_sta_rate_not_fixed:
            assert False, "STA rate is fixed, although it shouldn't be"
        elif not is_ap_rate_fixed and not is_sta_rate_not_fixed:
            assert False, "AP rate is not fixed and STA rate is fixed, should be reversed"

    # Step (4) - Shutdown.
    finally:
        ap.shutdown()
        sta.shutdown()
        channel.shutdown()
