import time

from WiFi.Source.Channel import Channel
from WiFi.Source.CHIP import CHIP
from WiFi.Source.visualizer import plot_wifi_summary

# Channel.
channel = Channel(channel_response=[1], snr_db=25)

# AP - Transmitter.
ap = CHIP(role='AP', identifier="AP")
ap.activation()
time.sleep(1)

# STA - Receiver.
sta = CHIP(role='STA', identifier="STA 1")
sta.activation()

# Sending message.
time.sleep(60)
text = """Joy, bright spark of divinity,\nDaughter of Elysium,\nFire-insired we trea"""
ap.mac.send_data_frame(data=text, destination_address=sta.mac._mac_address)

time.sleep(30)
ap.print_statistics()
sta.print_statistics()
plot_wifi_summary(ap, sta)

ap.shutdown()
sta.shutdown()
