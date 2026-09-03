"""Lightweight pure-Python image header and dimension extraction."""

from __future__ import annotations

import struct
from typing import Any


def parse_image_header(data: bytes) -> tuple[str, int, int, int] | None:
    """Parse format, width, height, and channels from image header bytes without external libraries.

    Returns (format_name, width, height, channels) or None if unparseable.
    """
    if len(data) < 10:
        return None

    # PNG
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 26:
        # IHDR chunk starts at byte 12 (length 4, type 4, width 4, height 4, bit depth 1, color type 1)
        width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
        # Color types: 0=grayscale (1ch), 2=RGB (3ch), 3=Palette (3ch), 4=Gray+Alpha (2ch), 6=RGBA (4ch)
        channel_map = {0: 1, 2: 3, 3: 3, 4: 2, 6: 4}
        channels = channel_map.get(color_type, 3)
        return "PNG", width, height, channels

    # GIF
    if (data.startswith(b"GIF87a") or data.startswith(b"GIF89a")) and len(data) >= 10:
        width, height = struct.unpack("<HH", data[6:10])
        return "GIF", width, height, 3

    # BMP
    if data.startswith(b"BM") and len(data) >= 30:
        width, height = struct.unpack("<ii", data[18:26])
        bpp = struct.unpack("<H", data[28:30])[0]
        channels = 4 if bpp == 32 else (3 if bpp >= 24 else 1)
        return "BMP", abs(width), abs(height), channels

    # JPEG
    if data.startswith(b"\xff\xd8"):
        idx = 2
        length = len(data)
        while idx < length:
            if data[idx] != 0xFF:
                break
            while idx < length and data[idx] == 0xFF:
                idx += 1
            if idx >= length:
                break
            marker = data[idx]
            idx += 1

            if marker in {0xD8, 0xD9, 0x01}:  # SOI, EOI, TEM
                continue

            if idx + 2 > length:
                break
            seg_len = struct.unpack(">H", data[idx:idx + 2])[0]
            if seg_len < 2 or idx + seg_len > length:
                break

            # SOF0 (0xC0) .. SOF15 (0xCF) except DHT (0xC4), JPG (0xC8), DAC (0xCC)
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                if idx + 8 <= length:
                    _, h, w, ch = struct.unpack(">BHHB", data[idx + 2:idx + 8])
                    return "JPEG", w, h, ch
            idx += seg_len

    return None


def extract_image_features(records: list[Any]) -> dict[str, Any]:
    """Extract deterministic image structural characteristics and header metadata."""
    if not records:
        return {
            "observed_images_count": 0,
            "image_bytes_available": False,
            "detected_formats": [],
            "dimensions_summary": {"min_width": 0, "max_width": 0, "min_height": 0, "max_height": 0, "aspect_ratio_mean": 0.0},
            "channels_distribution": {},
            "corrupt_images_count": 0,
        }

    sample = records[:32]
    num_images = len(sample)

    widths: list[int] = []
    heights: list[int] = []
    aspect_ratios: list[float] = []
    channels_count: dict[str, int] = {}
    formats: set[str] = set()
    corrupt_count = 0
    has_raw_bytes = False

    for item in sample:
        raw_bytes: bytes | None = None
        if isinstance(item, bytes):
            raw_bytes = item
            has_raw_bytes = True
        elif isinstance(item, dict):
            # Check if dict contains raw bytes or base64 or metadata
            if isinstance(item.get("bytes"), bytes):
                raw_bytes = item["bytes"]
                has_raw_bytes = True
            elif isinstance(item.get("image"), bytes):
                raw_bytes = item["image"]
                has_raw_bytes = True
            else:
                # Metadata-only reference (e.g. image path or format in dict)
                fmt = str(item.get("format") or item.get("extension") or "").upper()
                if fmt:
                    formats.add(fmt)
                if isinstance(item.get("width"), (int, float)) and isinstance(item.get("height"), (int, float)):
                    w, h = int(item["width"]), int(item["height"])
                    if w > 0 and h > 0:
                        widths.append(w)
                        heights.append(h)
                        aspect_ratios.append(round(w / h, 4))
                if isinstance(item.get("channels"), int):
                    ch_key = f"{item['channels']}ch"
                    channels_count[ch_key] = channels_count.get(ch_key, 0) + 1

        if raw_bytes:
            parsed = parse_image_header(raw_bytes)
            if parsed:
                fmt, w, h, ch = parsed
                formats.add(fmt)
                widths.append(w)
                heights.append(h)
                aspect_ratios.append(round(w / h, 4) if h else 1.0)
                ch_key = f"{ch}ch"
                channels_count[ch_key] = channels_count.get(ch_key, 0) + 1
            else:
                corrupt_count += 1

    dim_summary = {
        "min_width": min(widths) if widths else 0,
        "max_width": max(widths) if widths else 0,
        "min_height": min(heights) if heights else 0,
        "max_height": max(heights) if heights else 0,
        "aspect_ratio_mean": round(sum(aspect_ratios) / len(aspect_ratios), 4) if aspect_ratios else 0.0,
    }

    return {
        "observed_images_count": num_images,
        "image_bytes_available": has_raw_bytes,
        "detected_formats": sorted(formats),
        "dimensions_summary": dim_summary,
        "channels_distribution": dict(sorted(channels_count.items())),
        "corrupt_images_count": corrupt_count,
    }
