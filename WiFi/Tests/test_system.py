# Imports #
import time
from unittest.mock import patch
from WiFi.Source.chip import CHIP
from channel import Channel
from constants import *
from mac import MAC


def test_basic_association():
    """
    TODO: Complete the docstring.
    """

    # Setting AP, STA and channel.
    channel = Channel(channel_response=[1], snr_db=25)
    ap = CHIP(role='AP', identifier="AP")
    sta = CHIP(role='STA', identifier="STA 1")

    # Buffer time to allow for the association to happen.
    time.sleep(50)

    # Test criteria assertions.
    try:
        assert len(ap.mac._associated_sta) == 1
        assert ap.mac._associated_sta[0] == sta.mac._mac_address
        assert sta.mac._associated_ap == ap.mac._mac_address
    finally:
        ap.shutdown()
        sta.shutdown()
        channel.shutdown()


def test_send_data_when_associated():
    """
    TODO: Complete the docstring.
    """

    # Setting channel.
    channel = Channel(channel_response=[1], snr_db=25)

    with (patch('chip.MAC.beacon_broadcast', return_value=None),
          patch('chip.MAC.scanning', return_value=None)):
        # Setting the AP and STA.
        ap = CHIP(role='AP', identifier="AP")
        sta = CHIP(role='STA', identifier="STA 1")
        # Mocking association between AP and STA.
        ap.mac._associated_sta = [sta.mac._mac_address]
        sta.mac._associated_ap = ap.mac._mac_address

        # Sending the data message from AP to STA (DL).
        ap.send_text(text=MESSAGE)

        # Buffer time to allow the STA to receive and decode the data message.
        time.sleep(15)

        # Asserting that the message was successfully received.
        try:
            assert sta.mac._last_data.decode('utf-8') == MESSAGE
        finally:
            ap.shutdown()
            sta.shutdown()
            channel.shutdown()


def test_send_data_no_association():
    """
    TODO: Complete the docstring.
    """

    # Setting channel.
    channel = Channel(channel_response=[1], snr_db=25)

    with (patch('chip.MAC.beacon_broadcast', return_value=None),
          patch('chip.MAC.scanning', return_value=None)):
        # Setting the AP and STA.
        ap = CHIP(role='AP', identifier="AP")
        sta = CHIP(role='STA', identifier="STA 1")
        # Mocking association between AP and STA (AP only).
        ap.mac._associated_sta = [sta.mac._mac_address]

        # Sending the data message from AP to STA (DL).
        ap.send_text(text=MESSAGE)

        # Buffer time to allow the STA to receive and decode the data message.
        time.sleep(20)

        # Asserting that the message was successfully received.
        try:
            assert sta.mac._last_data is None
        finally:
            ap.shutdown()
            sta.shutdown()
            channel.shutdown()
