# WiFi Module

A software simulation of the IEEE 802.11 wireless LAN protocol stack. The module implements a full PHY layer (OFDM with BCC encoding), a MAC layer (frame management, scanning, authentication, association, RTS/CTS, WEP encryption), and a Channel model (multipath + AWGN). All components communicate over local TCP sockets, mirroring the hardware interfaces of a real chipset.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Settings](#settings)
- [Channel](#channel)
- [PHY Layer](#phy-layer)
- [MAC Layer](#mac-layer)
- [CHIP — Integration Class](#chip--integration-class)
- [Demo (main.py)](#demo-mainpy)

---

## Overview

The simulation models two IEEE 802.11 devices communicating through a shared channel:

```
[CHIP (AP)]                          [CHIP (STA)]
  └── MAC ─── MPIF ─── PHY            MAC ─── MPIF ─── PHY
                          └── TCP ──────┘        │
                               Channel           └── TCP ──> Channel
```

- **Channel**: TCP server on port `65535`. Applies multipath convolution and AWGN to signals before broadcasting to all connected clients.
- **PHY**: Handles OFDM transmission/reception. Connects to Channel via TCP. Interfaces with MAC via the MPIF (MAC-PHY Interface) socket bridge.
- **MAC**: Manages 802.11 frame exchange (management, control, data). Connects to PHY via MPIF.
- **CHIP**: Top-level integration object that instantiates and wires MAC + PHY together.

---

## Architecture

### Signal Flow (Transmit)
```
MAC → PSDU bits → PHY TX chain:
  Scramble → BCC encode → Puncture → Interleave → Modulate (BPSK/QPSK/16-QAM/64-QAM)
  → Pilot subcarrier insertion → IFFT → Add GI/window → Send to Channel
```

### Signal Flow (Receive)
```
Channel → PHY RX chain:
  STF correlation (frame detect) → LTF FFT (channel estimation)
  → SIGNAL field decode (rate/length) → DATA symbols:
      FFT → Equalize → Remove pilots → Demap → Deinterleave → Viterbi decode
      → Descramble → PSDU octets → MAC
```

### MAC Frame Exchange
```
Discovery: Beacon broadcast (AP) → Passive/Active Scan (STA)
Auth:       Probe Req → Probe Resp → Auth Req → Auth Resp
Assoc:      Assoc Req → Assoc Resp
Data:       RTS → CTS → Data → ACK  (or direct Data → ACK if below threshold)
```

---

## Project Structure

```
WiFi/
├── Settings/
│   └── wifi_settings.py        # All protocol constants and MCS parameters
├── Source/
│   ├── channel.py              # Channel simulation (TCP server, AWGN, multipath)
│   ├── phy.py                  # PHY layer (OFDM TX/RX chain, ~1375 lines)
│   ├── mac.py                  # MAC layer (frame exchange, security, ~1482 lines)
│   └── chip.py                 # Top-level CHIP integration class
├── Tests/
└── main.py                     # Demo script
```

---

## Settings

**File:** `Settings/wifi_settings.py`

### Network

| Constant | Value | Description |
|---|---|---|
| `HOST` | `'127.0.0.1'` | Loopback address for all TCP sockets |
| `CHANNEL_PORT` | `65535` | TCP port for the Channel server |
| `BROADCAST_ADDRESS` | `'FF:FF:FF:FF:FF:FF'` | IEEE broadcast MAC address |
| `SHORT_RETRY_LIMIT` | `7` | Max TX retries before dropping a frame |
| `AUTHENTICATION_ATTEMPTS` | `3` | Max auth attempts |

### Timing

| Constant | Description |
|---|---|
| `BEACON_INTERVAL` | Time between AP beacon frames |
| `PROBE_INTERVAL` | Active scan probe interval |

### Security

| Constant | Description |
|---|---|
| `SECURITY_ALGORITHMS` | Supported algorithms: `open-system`, `shared-key` (WEP) |

### BCC Convolutional Code

| Constant | Value | Description |
|---|---|---|
| `G1` | `[1,0,1,1,0,1,1]` | Generator polynomial 1 (133 octal) |
| `G2` | `[1,1,1,1,0,0,1]` | Generator polynomial 2 (171 octal) |

### Modulation and Coding Schemes (MCS)

| Data Rate | Modulation | Coding Rate | Description |
|---|---|---|---|
| 6 Mbps | BPSK | 1/2 | Lowest rate, most robust |
| 9 Mbps | BPSK | 3/4 | |
| 12 Mbps | QPSK | 1/2 | |
| 18 Mbps | QPSK | 3/4 | |
| 24 Mbps | 16-QAM | 1/2 | |
| 36 Mbps | 16-QAM | 3/4 | |
| 48 Mbps | 64-QAM | 2/3 | |
| 54 Mbps | 64-QAM | 3/4 | Highest rate |

### Preamble Constants
- `FREQUENCY_DOMAIN_STF` — Short Training Field (STF) frequency-domain sequence
- `FREQUENCY_DOMAIN_LTF` — Long Training Field (LTF) frequency-domain sequence

---

## Channel

**File:** `Source/channel.py`

### Class: `Channel`

A TCP server that sits between PHY instances. It applies physical channel effects before forwarding signals.

#### Constructor

```python
channel = Channel(channel_response=[1], snr_db=25)
```

| Parameter | Description |
|---|---|
| `channel_response` | Multipath impulse response (list of tap coefficients). `[1]` = ideal AWGN-only. |
| `snr_db` | Signal-to-noise ratio in dB |

#### `listen()`
Starts the TCP server on `CHANNEL_PORT`. Accepts PHY connections and spawns `handle_client()` threads.

#### `pass_signal(signal)`
Applies channel effects to a received signal:
1. **Multipath**: convolves signal with `channel_response`
2. **AWGN**: adds complex Gaussian noise scaled from `snr_db`

#### `broadcast(signal, sender)`
Forwards the processed signal to all connected PHY clients (excluding the sender).

#### `shutdown()`
Gracefully closes all client connections and the server socket.

---

## PHY Layer

**File:** `Source/phy.py` (~1375 lines)

### Class: `PHY`

Implements the full OFDM physical layer for IEEE 802.11a/g.

#### Constructor

```python
phy = PHY(role="AP")
```

#### TX Chain

| Method | Description |
|---|---|
| `tx_vector` setter | Receives PSDU + MCS parameters from MAC, triggers TX |
| `generate_preamble()` | Constructs STF + LTF via IFFT; LTF repeated twice for channel estimation |
| `generate_signal_symbol()` | Encodes rate/length: BCC(1/2) → interleave → BPSK → pilot insert → IFFT |
| `generate_data_symbol()` | Encodes data: scramble → BCC → puncture → interleave → modulate → pilot → IFFT |
| `generate_ppdu()` | Assembles PPDU (preamble + SIGNAL + DATA) with overlapping windows, sends to Channel |

#### RX Chain

| Method | Description |
|---|---|
| `detect_frame()` | STF cross-correlation; frame detected when correlation exceeds threshold `1.5` |
| `channel_estimation()` | FFT of received LTF symbols; estimates H[k] per subcarrier via interpolation |
| `decode_signal()` | Decodes SIGNAL field: FFT → equalize → BPSK demap → deinterleave → Viterbi → parity check |
| `decipher_data()` | Decodes N data OFDM symbols: FFT → equalize → remove pilots → demap → deinterleave → Viterbi → descramble |
| `convert_to_frequency_domain()` | Removes GI, applies FFT |
| `equalize_and_remove_pilots()` | Divides by estimated channel H[k], extracts data subcarriers |

#### OFDM Subcarrier Structure
- **Data subcarriers**: ±{1–26} excluding pilots
- **Pilot subcarriers**: −21, −7, +7, +21 (BPSK, known sequence)
- **Guard interval (GI)**: cyclic prefix of the last samples
- **Window**: raised-cosine windowing to reduce spectral leakage

#### Key Signal Processing Methods

| Method | Description |
|---|---|
| `generate_lfsr_sequence(seed)` | 7-bit LFSR scrambler (polynomial x⁷+x⁴+1) |
| `bcc_encode(bits)` | Rate-1/2 BCC with puncturing for 2/3 and 3/4 rates |
| `interleave(bits)` | Two-step permutation: frequency diversity + adjacent-bit separation |
| `subcarrier_modulation(bits, scheme)` | Gray-coded BPSK / QPSK / 16-QAM / 64-QAM |
| `pilot_subcarrier_insertion(data)` | Inserts ±1 BPSK pilots at subcarriers −21, −7, +7, +21 |
| `convert_to_time_domain(freq)` | IFFT + GI + windowing |
| `hard_decision_demapping(symbols, scheme)` | Nearest-constellation-point decision |
| `deinterleave(bits)` | Inverse of `interleave()` |
| `convolutional_decode_viterbi(bits)` | Viterbi decoder with K=7, supports punctured codes |

---

## MAC Layer

**File:** `Source/mac.py` (~1482 lines)

### Class: `MAC`

Implements the IEEE 802.11 MAC sublayer: frame generation, network discovery, authentication, association, and data transfer.

#### Constructor

```python
mac = MAC(role="AP", identifier="MyNetwork")
```

#### MAC Address

| Method | Description |
|---|---|
| `generate_mac_address()` | Generates a random unicast, locally-administered MAC address |

#### MPIF Interface

| Method | Description |
|---|---|
| `mpif_connection()` | Connects MAC to PHY via the MPIF TCP socket |
| `mpif_listen()` | Listens for incoming PHY primitives (Rx indications) |
| `transmission_queue()` | Processes the outbound TX queue, passing frames to PHY |

#### Network Discovery

| Method | Description |
|---|---|
| `beacon_broadcast()` | AP periodically broadcasts Beacon management frames |
| `scanning()` | STA performs passive scanning (20s listen) then active scanning (Probe Request) |
| `network_discovery()` | Top-level discovery coordinator |

#### Rate Selection

| Method | Description |
|---|---|
| `rate_selection()` | Selects MCS (modulation + coding) based on observed link quality |

#### Frame Controllers

| Method | Description |
|---|---|
| `controller()` | Top-level PHY primitive dispatcher |
| `management_controller(frame)` | Handles Beacon, Probe Request/Response, Auth, Association |
| `control_controller(frame)` | Handles ACK, RTS, CTS |
| `data_controller(frame)` | Handles Data frames and CRC verification |

#### Data Transfer

| Method | Description |
|---|---|
| `send_data_frame(payload)` | Sends a data frame; uses RTS/CTS if payload exceeds threshold |
| `send_acknowledgement_frame(dest)` | Sends an ACK frame to the destination |
| `wait_for_confirmation(frame)` | Retransmits up to `SHORT_RETRY_LIMIT` (7) times waiting for ACK |

#### Frame Construction

| Method | Description |
|---|---|
| `generate_psdu(payload)` | Converts payload bytes to bits and appends CRC-32 |
| `generate_mac_header(frame_type, dest, src)` | Builds the MAC header fields |
| `generate_frame_control_field(type, subtype, flags)` | Constructs the 2-byte Frame Control field |
| `cyclic_redundancy_check_32(data)` | CRC-32 using polynomial `0xEDB88320` |
| `convert_bits_to_bytes(bits)` | Bit array to byte array conversion |

#### Security (WEP)

| Method | Description |
|---|---|
| `encrypt_data(data, algorithm)` | Encrypts using `open-system` (none) or `shared-key` (WEP RC4) |
| `decrypt_data(data, algorithm)` | Decrypts the frame payload |
| `rc4_stream_cipher(key, data)` | RC4 KSA + PRGA stream cipher implementation |

WEP shared-key authentication uses the RC4 stream cipher with a randomly generated initialization vector (IV) prepended to the ciphertext.

---

## CHIP — Integration Class

**File:** `Source/chip.py`

### Class: `CHIP`

The top-level object representing a complete WiFi chipset. It creates and wires together a `PHY` and `MAC`, and manages the MPIF server socket that bridges them.

#### Constructor

```python
chip = CHIP(role="AP", identifier="MyNetwork")
```

#### `activation()`
Starts all background threads:
1. MPIF establishment (accepts PHY + MAC TCP connections)
2. MAC TX queue processing
3. Channel TCP connection (PHY connects to Channel)
4. Network discovery (scanning / beacon)

#### `establish_mpif()`
Accepts inbound connections from PHY and MAC on the MPIF server socket, then spawns bidirectional `forward_messages()` threads between them.

#### `forward_messages(source, destination)`
Relays all messages from `source` socket to `destination` socket (runs continuously in a thread).

#### `print_statistics()`
Prints a formatted table of MAC/PHY statistics (frames sent, received, retries, errors, etc.).

#### `shutdown()`
Gracefully closes all sockets and joins all threads.

---

## Demo (main.py)

```python
# Ideal channel (no multipath), 25 dB SNR
channel = Channel(channel_response=[1], snr_db=25)

# Start Access Point
ap = CHIP(role="AP", identifier="MyNetwork")
ap.activation()

# Start Station
sta = CHIP(role="STA", identifier="MyNetwork")
sta.activation()

# Wait for full 802.11 association handshake
time.sleep(60)

# Send a data payload (Schiller's "Ode to Joy" excerpt)
sta.mac.send_data_frame(payload="Freude, schöner Götterfunken...")

# Wait for ACK and delivery
time.sleep(30)

# Print link statistics
ap.print_statistics()
sta.print_statistics()

# Graceful teardown
ap.shutdown()
sta.shutdown()
channel.shutdown()
```