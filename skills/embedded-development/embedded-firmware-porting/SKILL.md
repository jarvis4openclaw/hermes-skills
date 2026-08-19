---
name: embedded-firmware-porting
description: Evaluate, implement, build, and validate firmware or embedded OS ports for unsupported microcontroller boards. Covers hardware identity matching, upstream source inspection, display/touch drivers, reproducible toolchains, artifact verification, and honest hardware-validation boundaries.
version: 1.0.1
category: embedded-development
metadata:
  hermes:
    tags: [firmware, embedded, micropython, esp32, lvgl, display, touch, porting]
    trigger_conditions:
      - "port firmware to a board"
      - "unsupported device firmware"
      - "build MicroPython for my device"
      - "LVGL board port"
      - "ESP32 display port"
      - "board not supported upstream"
      - "display driver for my board"
      - "touch controller driver"
      - "build firmware for esp32-s3"
      - "reproducible embedded build"
      - "evaluate porting feasibility"
      - "firmware for unknown dev board"
      - "flash image partition sizing"
      - "verify firmware artifact sha256"
      - "board module alias manufacturer"
---

# Embedded Firmware Porting

## Objective

Determine whether an unsupported board is a realistic port target, produce the strongest buildable image possible, and clearly separate compile-time proof from on-device validation.

## Not For
- **Adding a feature to an already-supported board** — if the board exists upstream, edit the board module directly → use the upstream contribution workflow.
- **Writing a brand-new display/touch driver from scratch** — only do this when no near-identical driver exists; prefer adapting an existing one (see Workflow step 6).
- **Application-level MicroPython/Arduino coding** (blinking LEDs, sensors on a supported board) — no porting involved → use the platform's own docs.
- **Bare-metal bring-up for a completely new SoC** (no upstream toolchain, no reference board) — that's silicon bring-up, not a port → out of scope.
- **Hardware repair / soldering / electrical diagnosis** — firmware porting assumes the board is electrically sound → use the vendor's hardware docs.

## Workflow

1. **Identify the board precisely.** Collect MCU, flash/PSRAM type and size, display controller and bus, touch controller and bus, pin assignments, reset/backlight polarity, resolution, and peripherals needed for minimum usability.
2. **Read the upstream porting guide and build scripts.** The live build script often contains requirements and partition assumptions omitted from prose documentation.
3. **Search current upstream source before writing a port.** Search board modules, detection logic, recent commits/issues/discussions, aliases, manufacturer names, and electrically equivalent models. A board may be newly supported under a vendor/product alias.
4. **Cross-check against a known-working firmware.** Existing Arduino/PlatformIO board definitions are excellent sources for pins, memory type, display inversion, touch address, and peripheral wiring.
5. **Establish feasibility by layers:**
   - MCU/toolchain can build and boot a serial REPL.
   - Display controller has a driver and the bus topology is supported.
   - Touch/input controller has a driver or a small protocol implementation is feasible.
   - Board detection or an explicit board selection can load the board module.
   - Flash/PSRAM and partition sizes fit the complete image.
6. **Prefer adapting an existing near-identical board module** over creating a new low-level driver.
7. **Build reproducibly** in an isolated worker/CT when the toolchain is large. Preserve source commit, build command, and logs.
8. **Verify the artifact** with file existence, size, checksum, and build success output.
9. **Do not call the port hardware-validated without flashing and testing the physical device.** A successful compile proves toolchain and source compatibility, not display colors, rotation, touch mapping, boot stability, or peripheral operation.

## Viability rubric

- **High confidence:** exact/electrically equivalent board module exists, drivers exist, memory configuration matches, and independent evidence shows the combination working.
- **Moderate confidence:** MCU and drivers exist, pins are known, but initialization/color/rotation/touch behavior needs device testing.
- **Low confidence:** unknown controller, unsupported bus topology, missing pinout, insufficient memory, or no way to recover/flash safely.

## Display and touch validation

For SPI displays, verify host, MOSI/MISO/SCLK, CS, DC, reset, backlight pin/polarity, frequency, width/height, init variant, byte order, RGB565 swapping, inversion, and rotation. A black screen can still mean a working firmware with incorrect initialization or backlight state.

Initialize touch before applying final display rotation when the driver framework maps coordinates from display rotation. Verify I²C address and reset timing. Similar controller families are not automatically protocol-identical.

## Build-system pitfalls

- Avoid recursive submodule initialization unless the upstream project explicitly requires it. If required, preflight disk and expect multi-gigabyte checkouts; report progress and alternatives rather than appearing stalled.
- Build scripts may freeze a whole filesystem, making a board Python module part of the firmware even when low-level drivers are compiled separately.
- Generic MCU targets are often correct when the board-specific behavior lives in runtime board modules.
- Preserve upstream source and make backups before local edits.

## Pitfalls

1. **Claiming hardware validation without flashing** — a successful compile proves toolchain/source compatibility only. Display colors, rotation, touch mapping, boot stability, and peripherals need the physical device. Recovery: label the result "compile-verified, hardware-pending" and list exactly what needs device testing.
2. **Missing board aliases** — a board may already be supported under a vendor/product alias or an electrically-equivalent model. Recovery: search upstream board modules, recent commits/issues, and manufacturer names BEFORE writing a port.
3. **Display black screen = not necessarily broken** — a black screen can mean working firmware with wrong init variant, RGB565 swap, inversion, or backlight polarity. Recovery: verify host/MOSI/MISO/SCLK, CS/DC/reset/backlight pins, polarity, frequency, width/height, init variant, byte order, and rotation before declaring failure.
4. **Touch applied before final display rotation** — the driver framework maps coordinates from display rotation; initializing touch first yields mirrored/rotated coordinates. Recovery: initialize touch after applying final display rotation, and verify I²C address + reset timing.
5. **Similar controller families assumed protocol-identical** — two "same family" touch/display controllers often differ in register layout. Recovery: confirm the exact datasheet command set, don't copy register values from a sibling controller.
6. **Recursive submodule init blowing the disk** — multi-GB checkouts stall builds and fill the filesystem silently. Recovery: preflight disk space and submodule count, report progress, or avoid recursion unless upstream explicitly requires it.
7. **Build "frozen" board modules mixed into firmware** — the build script may freeze a Python board module into the image while low-level drivers compile separately. Recovery: check the build manifest/partition table to see exactly what landed in the image.
8. **Partition sizing mismatch** — flash/PSRAM and partition sizes must fit the complete image; an undersized partition fails at flash time, not build time. Recovery: verify flash/PSRAM type and size, and partition table layout against the board specs.
9. **Artifact reported without checksum** — file existence and size don't prove integrity. Recovery: always report artifact path, size, and SHA-256, plus the source commit and exact build target.
10. **No safe flash/recovery path** — flashing an unknown board with no documented recovery can brick it. Recovery: only provide flash instructions after confirming the exact image layout, and always include the recovery path first.

## Reporting

Report:

- confidence and evidence
- what is already upstream versus locally added
- source commit and exact build target
- artifact path, size, and SHA-256
- features expected to work
- features requiring physical testing
- safe flash/recovery instructions only after confirming the exact image layout

See `references/micropythonos-esp32-display-port.md` for a concrete MicroPythonOS/LVGL ESP32-S3 display-board evaluation pattern.
