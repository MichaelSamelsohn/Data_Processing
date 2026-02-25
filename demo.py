"""
Script Name - demo.py

Purpose - Project demo combining all three modules:
    (1) Downloads the APOD (Astronomy Picture Of the Day) image using the NASA API.
    (2) Applies image processing transformations: grayscale conversion, Gaussian blur, and Sobel edge detection.
    (3) Transfers a processed image thumbnail from AP to STA via the WiFi simulation.
    (4) Displays the full pipeline — original image, processing stages, and the WiFi-received result.

Created by Michael Samelsohn, 24/02/26.
"""

# Imports #
import base64
import io
import time
from datetime import date

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image as PILImage

from Image_Processing.Source.Basic.common import convert_to_grayscale
from Image_Processing.Source.Advanced.spatial_filtering import blur_image, sobel_filter
from NASA_API.Source.apod import APOD
from WiFi.Source.channel import Channel
from WiFi.Source.chip import CHIP


def _section(title: str):
    """Print a formatted section header to the console."""
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}\n")


# ── Stage 1: Download the APOD Image ──────────────────────────────────────── #

_section("Stage 1 — NASA API: Downloading APOD Image")

today = date.today().strftime("%Y-%m-%d")
apod = APOD(date=today, hd=False)
success = apod.astronomy_picture_of_the_day()

if not success:
    print("[Demo] APOD download failed. Exiting.")
    exit(1)

image_path = apod.apod_image
print(f"[APOD] Image downloaded: {image_path}")


# ── Stage 2: Image Processing ─────────────────────────────────────────────── #

_section("Stage 2 — Image Processing: Transformations")

# Load the downloaded image as a normalized float64 numpy array.
pil_image = PILImage.open(image_path).convert("RGB")
image_array = np.array(pil_image, dtype=np.float64) / 255.0

# (a) Grayscale conversion using the NTSC formula.
gray_image = convert_to_grayscale(image=image_array)
print("[Processing] Grayscale conversion complete.")

# (b) Gaussian blur — reduces high-frequency noise before edge detection.
blurred_image = blur_image(
    image=gray_image,
    filter_type='gaussian',
    filter_size=5,
    padding_type='zero',
    sigma=1.0,
    normalization_method='unchanged'
)
print("[Processing] Gaussian blur (5×5, σ=1.0) complete.")

# (c) Sobel edge detection — highlights structural boundaries in the image.
sobel_result = sobel_filter(image=gray_image, padding_type='zero', normalization_method='stretch')
edge_magnitude = sobel_result['Magnitude']
print("[Processing] Sobel edge detection complete.")


# ── Stage 3: WiFi Transfer ────────────────────────────────────────────────── #

_section("Stage 3 — WiFi: Transmitting Image Thumbnail (AP → STA)")

# Encode a 32×32 thumbnail of the Sobel edge image as a base64 PNG string.
# A compact thumbnail is used to keep the WiFi payload manageable.
thumbnail_array = (np.clip(edge_magnitude, 0, 1) * 255).astype(np.uint8)
thumbnail_pil = PILImage.fromarray(thumbnail_array).resize((32, 32), PILImage.LANCZOS)
buffer = io.BytesIO()
thumbnail_pil.save(buffer, format="PNG")
encoded_payload = base64.b64encode(buffer.getvalue()).decode('utf-8')

print(f"[WiFi] Payload size: {len(encoded_payload)} characters (base64 PNG, 32×32 px)")

# Initialize the WiFi channel and both chips.
channel = Channel(channel_response=[1], snr_db=25)

ap = CHIP(role='AP', identifier="AP")
ap.activation()
time.sleep(1)

sta = CHIP(role='STA', identifier="STA 1")
sta.activation()

# Allow time for the full AP-STA association handshake to complete
# (passive scan → probe → authentication → association).
print("[WiFi] Waiting for AP-STA association (60 seconds)...")
time.sleep(45)

# AP transmits the encoded image thumbnail to the STA.
# The MAC layer automatically splits the payload into 256-byte chunks, each sent and ACK'ed individually.
num_chunks = -(-len(encoded_payload.encode('utf-8')) // 256)  # Ceiling division.
transfer_wait = max(30, num_chunks * 10)
print(f"[WiFi] Transmitting encoded thumbnail from AP to STA ({num_chunks} chunk(s))...")
ap.mac.send_data_frame(data=encoded_payload, destination_address=sta.mac._mac_address)

# Allow time for all chunks and their ACKs to complete.
print(f"[WiFi] Waiting for transfer to complete ({transfer_wait} seconds)...")
time.sleep(transfer_wait)

ap.print_statistics()
sta.print_statistics()

ap.shutdown()
sta.shutdown()
print("[WiFi] Simulation shut down.")


# ── Stage 4: Display Results ──────────────────────────────────────────────── #

_section("Stage 4 — Results: Processing Pipeline & WiFi Transfer")

if not sta.mac._rx_buffer:
    print("[Demo] No data received by STA — WiFi transfer may not have completed.")
    exit(1)

# Reassemble and decode the base64 payload accumulated across all received DATA frames.
received_base64 = sta.mac._rx_buffer.decode('utf-8')
decoded_bytes = base64.b64decode(received_base64)
received_image = np.array(PILImage.open(io.BytesIO(decoded_bytes)))

# Plot the full pipeline in a single figure.
fig, axes = plt.subplots(1, 5, figsize=(24, 5))

axes[0].imshow(image_array)
axes[0].set_title("Original\n(APOD)", fontsize=11)
axes[0].axis("off")

axes[1].imshow(gray_image, cmap='gray')
axes[1].set_title("Grayscale", fontsize=11)
axes[1].axis("off")

axes[2].imshow(blurred_image, cmap='gray')
axes[2].set_title("Gaussian Blur\n(5×5, σ=1.0)", fontsize=11)
axes[2].axis("off")

axes[3].imshow(edge_magnitude, cmap='gray')
axes[3].set_title("Sobel Edges\n(AP: Transmitted)", fontsize=11)
axes[3].axis("off")

axes[4].imshow(received_image, cmap='gray')
axes[4].set_title("STA: Received\n(WiFi Decoded)", fontsize=11)
axes[4].axis("off")

fig.suptitle(
    "Data Processing Demo — NASA API  →  Image Processing  →  WiFi Transfer",
    fontsize=13,
    fontweight='bold'
)
plt.tight_layout()
plt.show()

print("\n[Demo] Complete.")