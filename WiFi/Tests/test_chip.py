# Imports #
import socket

from WiFi.Settings.wifi_settings import *
from WiFi.Source.chip import CHIP


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
    chip = CHIP(role='', identifier="TEST_CHIP")

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

