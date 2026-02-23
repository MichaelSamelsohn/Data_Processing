# Utilities Module

A collection of cross-cutting utilities used across all modules in the Data_Processing project. Provides a custom Logger with color output and log masking, a set of function decorators for profiling and documentation tracing, and an Email class for SMTP-based notification.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Logger](#logger)
- [ColorFormatter](#colorformatter)
- [MaskedFilter](#maskedfilter)
- [Decorators](#decorators)
- [Email](#email)

---

## Overview

All modules in the project share the same Logger instance configured via `Utilities/logger.py`. Decorators from `Utilities/decorators.py` are applied to core processing functions to add runtime measurement and textbook/article citation logging without modifying function bodies.

---

## Project Structure

```
Utilities/
├── logger.py       # Logger, ColorFormatter, MaskedFilter
├── decorators.py   # measure_runtime, log_suppression, book_reference, article_reference
└── email.py        # Email class for SMTP notification
```

---

## Logger

**File:** `logger.py`

### Class: `Logger(logging.Logger)`

Extends the standard `logging.Logger` with color output, custom log levels, pattern masking, runtime property-driven handler reconfiguration, and structured data printing.

#### Initialization

```python
from Utilities.logger import Logger
log = Logger(name="my_module")
```

#### Properties

All properties automatically rebuild the logger's handlers when changed.

| Property | Description |
|---|---|
| `log_level` | Logging level (e.g., `logging.DEBUG`, `logging.INFO`) |
| `color_scheme` | Enables or disables ANSI color output |
| `format_string` | Custom log record format string |
| `format_time` | Timestamp format string |
| `masked_patterns` | List of regex patterns to mask in log output |
| `stream_handler` | Controls whether a `StreamHandler` is attached |
| `file_handler` | Controls whether a `FileHandler` is attached |
| `file_name` | Path to the log file (used when `file_handler=True`) |
| `level_name_only` | If `True`, only the level name is colored; otherwise the full line is colored |

#### Custom Log Levels

```python
log.add_custom_log_level(level_name="apod", level_number=11)
```

Dynamically registers a new log level and adds a corresponding method (e.g., `log.apod(...)`) to the class. Used by the NASA_API module to create per-API log levels.

#### `print_data(data, level)`
Structured output for common Python types:

| Type | Behavior |
|---|---|
| `list` | Logs each element on a separate line with index |
| `dict` | Logs each key-value pair |
| `str` / `int` / `float` | Logs as a single value |

#### Internal: `__set_handlers()`
Rebuilds all attached handlers from scratch whenever any logging property is changed. Applies `ColorFormatter` and `MaskedFilter` to each handler.

---

## ColorFormatter

**File:** `logger.py`

### Class: `ColorFormatter(logging.Formatter)`

A `logging.Formatter` subclass that adds ANSI color codes to log output.

#### Supported Colors by Level

| Level | Color |
|---|---|
| `DEBUG` | Cyan |
| `INFO` | Green |
| `WARNING` | Yellow |
| `ERROR` | Red |
| `CRITICAL` | Bold Red |
| Custom levels (e.g., `apod`, `epic`) | Module-specific colors |

#### Coloring Modes

Controlled by the `level_name_only` flag on the parent `Logger`:
- **`level_name_only=True`**: Only the level name portion of the log line is colored.
- **`level_name_only=False`**: The entire log line is colored.

---

## MaskedFilter

**File:** `logger.py`

### Class: `MaskedFilter(logging.Filter)`

A `logging.Filter` that replaces sensitive patterns in log messages with a masked string before output.

#### Usage

```python
log.masked_patterns = [r"\d{4}-\d{4}-\d{4}-\d{4}"]  # Mask credit card numbers
```

#### `filter(record)`
Iterates over all registered regex patterns and applies `re.sub()` to `record.getMessage()`, replacing matches with `"****"` (or a configured mask string).

---

## Decorators

**File:** `decorators.py`

Four decorators used throughout the project to add cross-cutting behavior without modifying function logic.

### `@measure_runtime`

Measures and logs the wall-clock execution time of the decorated function.

```python
@measure_runtime
def convolution_2d(image, kernel, ...):
    ...
```

After the function returns, logs:
```
convolution_2d executed in 0.042 seconds
```

### `@log_suppression(level)`

Temporarily raises the logger's level to `level` during the function call, then restores the original level.

Used to silence verbose recursive functions (e.g., connected-component labeling) that would otherwise flood the log with thousands of DEBUG entries.

```python
@log_suppression(logging.WARNING)
def connected_component_8(image, ...):
    ...
```

### `@book_reference(book, reference)`

Logs a textbook citation immediately before the function executes. Used throughout `Image_Processing` to trace every algorithm back to its source in *"Digital Image Processing"* by Gonzales & Woods.

```python
@book_reference(
    book=GONZALES_WOODS_BOOK,
    reference="Chapter 3.5 - Smoothing Spatial Filters, p.164-175"
)
def blur_image(image, filter_type, ...):
    ...
```

Logs before call:
```
[Reference] Digital Image Processing (4th ed.) — Chapter 3.5 - Smoothing Spatial Filters, p.164-175
```

### `@article_reference(article)`

Same as `@book_reference` but for journal/conference paper citations. Used for algorithms sourced from research literature (e.g., Harris corner detection, Zhang-Suen thinning).

```python
@article_reference(article="Zhang & Suen (1984) - A Fast Parallel Algorithm for Thinning Digital Patterns")
def parallel_sub_iteration_thinning(image, method):
    ...
```

---

## Email

**File:** `email.py`

### Class: `Email`

Sends email notifications via SMTP, with support for file attachments. Configured for Gmail by default.

#### Constructor

```python
email = Email(
    sender="sender@gmail.com",
    recipients=["recipient@gmail.com"],
    subject="Notification",
    body="Processing complete.",
    app_password="your_gmail_app_password"
)
```

| Parameter | Default | Description |
|---|---|---|
| `server_host` | `"smtp.gmail.com"` | SMTP server hostname |
| `server_port` | `587` | SMTP port (STARTTLS) |
| `sender` | required | Sender Gmail address |
| `recipients` | required | List of recipient addresses |
| `subject` | `""` | Email subject line |
| `body` | `""` | Plain-text email body |
| `app_password` | required | Gmail app password (not account password) |
| `attachments` | `[]` | List of file paths to attach |

#### `send()`
Builds a `MIMEMultipart` message, attaches files, establishes a STARTTLS connection, authenticates, and sends the email.

Workflow:
1. Validate parameters via `_check_essential_parameters()`
2. Build `MIMEMultipart("mixed")` with `MIMEText` body
3. For each attachment: read file, wrap in `MIMEBase`, encode as base64, attach
4. `smtplib.SMTP(host, port)` → `starttls()` → `login()` → `sendmail()`

#### `_check_essential_parameters()`
Validates:
- `server_host` is a non-empty string
- `server_port` is an integer in a valid range
- `sender` and all `recipients` pass email format regex
- `_check_email_address_validity()` enforces **Gmail domain only** (`@gmail.com`)

#### Gmail App Password

Gmail requires an **App Password** (not the regular account password) when using SMTP with two-factor authentication enabled. Generate one at: Google Account → Security → App Passwords.

**Example:**
```python
email = Email(
    sender="mybot@gmail.com",
    recipients=["user@gmail.com"],
    subject="Job Complete",
    body="Image processing finished successfully.",
    app_password="abcd efgh ijkl mnop",
    attachments=[r"NASA_API/Images/APOD_2025-01-01.JPG"]
)
email.send()
```