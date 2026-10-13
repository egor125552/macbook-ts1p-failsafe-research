# SMC firmware analysis

## Matching image

The isolated analysis used:

```text
AppleSMCFirmware_H16_4-7372.1.3.j713.REL
SHA-256 010387bee26ac2937f2b835a9b54c1bde251334cac8ed23b12080d71bd8623fa
```

The image is not distributed in this repository.

The running Mac's SMC firmware version (`RVER`) was checked against the extracted image version. The compressed SMC key catalog was then decoded by executing the firmware's own catalog-enumeration routine in an isolated Unicorn instance.

All **2265** extracted key names and their order matched the live SMC catalog. This gives a strong anchor for mapping internal descriptors and value storage to live four-character keys.

## Ts1P descriptor mapping

For this image:

| Item | Offset / value |
|---|---|
| Input index | `12` |
| Input descriptor | `0x84270` |
| value-pointer area | `0x7b910` |
| mapped value | `0xa0e70` |
| live key | `Ts1P` |

The descriptor is part of a 32-byte-per-input structure beginning around `0x840f0`; input 12 therefore lands at the documented descriptor location.

## Fault formation

Function near `0x3b4b4` updates the input fault/debounce state. The persistent fault is stored at descriptor byte `+0x12`.

This matters because the fail-safe is **not** triggered by the mathematical condition `temperature == 0`. The controller tracks whether a required input is successfully delivering usable data, including fault/debounce state.

A separate update path near `0x33c6c` packs persistent input fault bits into the exported mask array near `0x9ca18`.

For the first 32 inputs, exported `SEB0` therefore represents the first fault word. Input 12 becomes bit 12:

```text
1 << 12 = 0x00001000
```

Live value:

```text
SEB0 = 0x00001000
```

Current/transient errors are also visible in `SES0`. During the captured fault:

```text
SES0 = 0x00001800
```

which contains bits 11 and 12, corresponding to the two adjacent currently failing inputs mapped to Ts0P/Ts1P. Only input 12 remained in the captured persistent `SEB0` mask.

## Required-input lists

The package required-input list is near `0x89878`, contains 42 entries, and includes `{type 1, index 12}`.

The utility required-input list near `0x87c80` also includes input 12.

Function near `0x3b448` tests the required-input set and reports a fault condition when a listed descriptor carries the persistent input-fault state.

## Fixed fail-safe constants

The policy fragment near:

```text
0x39b4c … 0x39ba0
```

selects between normal computed limits and fixed fallback limits. The fallback data referenced near `0x87130` resolves to:

```text
package fallback = 2.0 W
utility fallback = 2.5 W
```

Normal live pre-fault values on the affected machine:

```text
voPp = 65.0 W
voUp = 30.0 W
```

Final live values after the required-input policy:

```text
xPPT = 2.0 W
xUPT = 2.5 W
```

Result storage around `0x87918` was mapped to xPPT/xUPT. Function near `0x3a180` transports the final values onward through PTD, with xPPT associated with C01 and xUPT with C02.

## Isolated causal replay

`tools/smc_failsafe_replay.py` executes the real identified policy fragment from a user-supplied matching firmware image. It reconstructs only the relevant descriptor fault bytes from captured masks.

Observed result:

| Experiment | package | utility | fail-safe state |
|---|---:|---:|---:|
| Ts1P fault present | 2.0 W | 2.5 W | `0x12` |
| only Ts1P fault cleared | 65.0 W | 30.0 W | `0` |

This experiment never opens AppleSMC and cannot modify a live Mac.

## Diagnostic reset command discovered in firmware

A separate diagnostic mechanism was identified around the `MSFL` / `MSFN` command path. In isolated memory, command 11 clears the selected input's current error counters, debounce state and persistent fault, allowing future measurements to be attempted again.

A replay of that command is included as `tools/smc_reset_command_replay.py`.

On the live Mac, `MSFL`, `MSFN`, `Ts1P`, `SEB0` and `xPPT` are not writable through the ordinary AppleSMC interface. Even no-op/same-value probes were rejected by the SMC with internal result 134. Therefore the isolated command is **not presented as a live workaround**.

## Endianness note for `hex_` keys

The SMC image read path near `0x2d338…0x2d360` produces the exported `hex_` byte sequence observed through the interface. The captured raw bytes:

```text
SEB0 raw = 00 00 10 00
```

correspond to numerical mask `0x00001000`, i.e. bit 12. Interpreting those four printed bytes in the opposite (little-endian) direction would incorrectly call this bit 20.

## What this analysis does not establish

Firmware names and input mappings identify the logical SMC input. They do not by themselves identify the physical sensor package, board connector or mechanical location on J713AP. That still requires hardware-level mapping or a controlled service experiment.
