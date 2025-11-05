import time

from WiFi.Source.channel import Channel
from WiFi.Source.chip import CHIP

# Channel.
channel = Channel(channel_response=[1], snr_db=25)

# AP - Transmitter.
ap = CHIP(role='AP', identifier="AP")

# STA - Receiver.
sta = CHIP(role='STA', identifier="STA 1")
time.sleep(1)

# Sending message.
time.sleep(60)
text = """Joy, bright spark of divinity,\nDaughter of Elysium,\nFire-insired we trea"""
ap.mac.send_text(text=text)
time.sleep(1000)

ap.shutdown()
sta.shutdown()
channel.shutdown()
