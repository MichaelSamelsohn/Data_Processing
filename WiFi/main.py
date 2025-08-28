import time

from WiFi.Source.channel import Channel
from WiFi.Source.chip import CHIP

# Channel.
channel = Channel(channel_response=[1], snr_db=25)

# AP - Transmitter.
ap = CHIP(role='AP', identifier="AP")
ap.mac.phy_rate = 36
time.sleep(1)

# STA - Receiver.
sta = CHIP(role='STA', identifier="STA 1")
time.sleep(1)

# Sending message.
time.sleep(75)
text = """Joy, bright spark of divinity,\nDaughter of Elysium,\nFire-insired we trea"""
ap.send_text(text=text)
time.sleep(1000)
