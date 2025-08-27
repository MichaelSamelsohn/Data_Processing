import time

from Settings.settings import log
from Signals.wifi import MPIF, CHIP
from Signals.channel import Channel
from debug import plot_rf_signal
from debug import plot_constellation_mapping


log.log_level = 20

# Channel.
channel = Channel(channel_response=[1], snr_db=25)

# AP - Transmitter.
ap = CHIP(role='AP')
ap.mac.phy_rate = 36
time.sleep(1)

# STA - Receiver.
sta = CHIP(role='STA')
time.sleep(1)

# Sending message.
time.sleep(75)
text = """Joy, bright spark of divinity,\nDaughter of Elysium,\nFire-insired we trea"""
ap.send_text(text=text)
time.sleep(1000)
