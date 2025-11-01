# Imports #
import time
from unittest.mock import patch
import pytest
from WiFi.Source.chip import CHIP
from channel import Channel
from constants import *
from mac import MAC


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
        assert len(ap.mac._associated_sta) == 1
        assert ap.mac._associated_sta[0] == sta.mac._mac_address
        assert sta.mac._associated_ap == ap.mac._mac_address
    # Step (4) - Shutdown.
    finally:
        ap.shutdown()
        sta.shutdown()
        channel.shutdown()


def test_send_data_when_associated():
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
            assert sta.mac._last_data.decode('utf-8') == MESSAGE
        # Step (6) - Shutdown.
        finally:
            ap.shutdown()
            sta.shutdown()
            channel.shutdown()


def test_send_data_no_association():
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
            assert sta.mac._last_data is None
        # Step (5) - Shutdown.
        finally:
            ap.shutdown()
            sta.shutdown()
            channel.shutdown()
