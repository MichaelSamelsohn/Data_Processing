# Imports #
import time
import random
import string
import pytest
import socket

from unittest.mock import patch
from WiFi.Settings.wifi_settings import *
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

    ap.activation()
    sta.activation()

    # Step (2) - Buffer time to allow for the association to happen.
    time.sleep(60)

    # Step (3) - Check that AP and STA are authenticated and associated (both sides).
    try:
        assert len(ap.mac._associated_sta) == 1,                           "AP is not associated with STA"
        assert ap.mac._encryption_type[str(sta.mac._mac_address)] == authentication_algorithm, \
            "Encryption method not saved for AP"
        assert ap.mac._associated_sta[0] == sta.mac._mac_address,          "AP is not associated with STA"
        assert sta.mac._associated_ap == ap.mac._mac_address,              "STA is not associated with AP"
        assert sta.mac._encryption_type[str(ap.mac._mac_address)] == authentication_algorithm, \
            "Encryption method not saved for AP"

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

    ap.activation()
    sta.activation()

    # Step (2) - Buffer time to allow for several authentication failures to happen.
    time.sleep(120)

    # Step (3) - Check that AP and STA are not authenticated (both sides) and AP is blacklisted for STA.
    try:
        assert len(ap.mac._authenticated_sta) == 0, "AP is authenticated with STA, although it shouldn't be"
        assert ap.mac._encryption_type == {},       "AP encryption dictionary is not empty"
        assert sta.mac._authenticated_ap is None,      "STA is authenticated with AP, although it shouldn't be"
        assert sta.mac._encryption_type == {},      "STA encryption dictionary is not empty"
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
        ap.mac._encryption_type[str(sta.mac._mac_address)] = "open-system"
        sta.mac._associated_ap = ap.mac._mac_address
        sta.mac._encryption_type[str(ap.mac._mac_address)] = "open-system"

        ap.activation()
        sta.activation()

        # Step (3) - Sending a random data (below RTS-CTS threshold) message from AP to STA (DL).
        random_message = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation,
                                                k=RTS_CTS_THRESHOLD - 1))
        ap.mac.send_data_frame(data=random_message, destination_address=sta.mac._mac_address)

        # Step (4) - Buffer time to allow for the data to be sent and received.
        time.sleep(15)

        # Step (5) - Asserting that the message was received successfully.
        try:
            assert sta.mac._last_data.decode('utf-8') == random_message, ("Received message is not the same as "
                                                                          "original one")

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
        ap.mac._encryption_type[str(sta.mac._mac_address)] = "open-system"

        ap.activation()
        sta.activation()

        # Step (2) - Sending the data message from AP to STA (DL).
        ap.mac.send_data_frame(data=MESSAGE, destination_address=sta.mac._mac_address)

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
    sta = CHIP(role='STA', identifier="STA 1")

    ap.mac.phy_rate = 6
    ap.mac.is_fixed_rate = True
    sta.mac.phy_rate = 6
    sta.mac.is_fixed_rate = False

    ap.activation()
    sta.activation()

    # Step (2) - Set a timeframe for the STA to change its rate.
    is_ap_rate_fixed = True
    is_sta_rate_not_fixed = False
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


def test_rts_cts_mechanism():
    """
    Test purpose - Basic functionality of RTS-CTS mechanism.
    Criteria - Send a data frame above the RTS-CTS threshold and check that RTS-CTS mechanism is used.

    Test steps:
    1) Set the channel, AP and STA with patched advertisement functionality.
    2) Mock association between AP and STA.
    3) Send a random data message (above RTS-CTS threshold) from STA to AP (UL).
    4) Set a timeframe for the AP to receive and decipher the data.
    5) Assert that the message was received correctly on the STA side and RTS-CTS mechanism was used.
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
        ap.mac._encryption_type[str(sta.mac._mac_address)] = "open-system"
        sta.mac._associated_ap = ap.mac._mac_address
        sta.mac._encryption_type[str(ap.mac._mac_address)] = "open-system"

        ap.activation()
        sta.activation()

        # Step (3) - Sending a random data message (above RTS-CTS threshold) from STA to AP (UL).
        random_message = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation,
                                                k=RTS_CTS_THRESHOLD + 1))
        sta.mac.send_data_frame(data=random_message, destination_address=ap.mac._mac_address)

        # Step (4) - Set a timeframe for the data to be sent and received with RTS-CTS.
        is_rts_cts_active = False
        try:
            for _ in range(30):
                if sta.mac._is_rts_cts:
                    # Raise relevant flag.
                    is_rts_cts_active = True

                # Buffer time between consecutive checks.
                time.sleep(1)

            # Step (5) - Asserting that the message was received successfully and RTS-CTS mechanism was used.
            assert ap.mac._last_data.decode('utf-8') == random_message, ("Received message is not the same as "
                                                                         "original one")
            assert is_rts_cts_active is True, "RTS-CTS mechanism wasn't used"

        # Step (6) - Shutdown.
        finally:
            ap.shutdown()
            sta.shutdown()
            channel.shutdown()


def test_rts_cts_configuration():
    """
    Test purpose - Basic functionality of setting the RTS-CTS mechanism to 'always'.
    Criteria - Set RTS-CTS mechanism to always and send data frames lower than RTS-CTS threshold. The frame is to be
    sent with RTS-CTS mechanism.

    Test steps:
    1) Set the channel, AP and STA with patched advertisement functionality. STA is configured with RTS-CTS always.
    2) Mock association between AP and STA.
    3) Send a random data message (below RTS-CTS threshold) from STA to AP (UL).
    4) Set a timeframe for the AP to receive and decipher the data.
    5) Assert that the message was received correctly on the STA side and RTS-CTS mechanism was used.
    6) Shutdown (to avoid unnecessary data leaks to next tests).
    """

    # Step (1) - Setting channel, AP and STA (with patched advertisement functionality). STA is configured with RTS-CTS.
    channel = Channel(channel_response=[1], snr_db=25)
    with (patch('chip.MAC.beacon_broadcast', return_value=None),
          patch('chip.MAC.scanning', return_value=None)):
        # Setting the AP and STA.
        ap = CHIP(role='AP', identifier="AP")
        sta = CHIP(role='STA', identifier="STA 1")
        sta.mac.is_always_rts_cts = True

        # Step (2) - Mocking association between AP and STA.
        ap.mac._associated_sta = [sta.mac._mac_address]
        ap.mac._encryption_type[str(sta.mac._mac_address)] = "open-system"
        sta.mac._associated_ap = ap.mac._mac_address
        sta.mac._encryption_type[str(ap.mac._mac_address)] = "open-system"

        ap.activation()
        sta.activation()

        # Step (3) - Sending a random data message (below RTS-CTS threshold) from STA to AP (UL).
        random_message = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation,
                                                k=RTS_CTS_THRESHOLD - 1))
        sta.mac.send_data_frame(data=random_message, destination_address=ap.mac._mac_address)

        # Step (4) - Set a timeframe for the data to be sent and received with RTS-CTS.
        is_rts_cts_active = False
        try:
            for _ in range(30):
                if sta.mac._is_rts_cts:
                    # Raise relevant flag.
                    is_rts_cts_active = True

                # Buffer time between consecutive checks.
                time.sleep(1)

            # Step (5) - Asserting that the message was received successfully and RTS-CTS mechanism was used.
            assert ap.mac._last_data.decode('utf-8') == random_message, ("Received message is not the same as "
                                                                         "original one")
            assert is_rts_cts_active is True, "RTS-CTS mechanism wasn't used"

        # Step (6) - Shutdown.
        finally:
            ap.shutdown()
            sta.shutdown()
            channel.shutdown()


def test_shutdown():
    """
    Test purpose - Basic functionality of chip shutdown.
    Criteria - Shutdown closes all sockets of a chip, MAC, PHY and MPIF.

    Test steps:
    1) Set channel dummy socket (for the PHY) and test chip (not designated as AP/STA to avoid advertising).
    2) Preform the shutdown.
    3) Checking that all chip sockets (MAC, PHY and MPIF) were closed.
    4) Close the dummy channel socket.
    """

    # Step (1) - Setting channel and test chip (no designation as AP/STA to avoid advertising).
    # Note - Dummy channel is set so that the PHY socket is able to connect to something.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, CHANNEL_PORT))
    server.listen()
    chip = CHIP(role='', identifier="identifier")

    # Step (2) - Preforming the shutdown.
    chip.shutdown()

    # Step (3) - Checking that all chip sockets were closed.
    try:
        assert chip.mpif.server._closed
        assert chip.phy._mpif_socket._closed
        assert chip.phy._channel_socket._closed
        assert chip.mac._mpif_socket._closed
    # Step (4) - Closing the dummy channel socket.
    finally:
        server.close()
