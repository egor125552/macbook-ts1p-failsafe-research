# Research tools

These are original helper programs written during the investigation. They are intentionally small and auditable.

## Read-only live tools

### `read_smc_status.c`

Reads SMC key metadata and values through the ordinary AppleSMC user-client interface. It checks both the IOKit return value and the SMC's internal result field.

### `powerlog_extract.py`

Extracts selected SMC series from PowerLog SQLite databases in read-only mode.

### `fault_decode.py`

Decodes exported SMC input-fault masks and locks down the byte/bit interpretation used for `SEB0` / `SES0`.

## Official restore-image bootstrap

### `fetch_official_restore.py`

Pins the exact `Mac16,12` / build `26A428` restore image to its official `updates.cdn-apple.com` URL, expected byte size and SHA-256. It can print the URL, verify an existing IPSW, or download/resume the roughly 26.6 GB IPSW and verify it before use. No Apple binary is stored in this repository.

```sh
python3 tools/fetch_official_restore.py --url-only
python3 tools/fetch_official_restore.py --download ./downloads
python3 tools/fetch_official_restore.py --verify ./downloads/UniversalMac_27.0_26A428_Restore.ipsw
```

## Offline firmware tools

These never communicate with the live SMC.

### `smc_failsafe_replay.py`

Executes the identified fail-safe policy fragment from a user-supplied matching SMC firmware image. It verifies the known SHA-256 by default and demonstrates the Ts1P-fault causal effect.

### `smc_reset_command_replay.py`

Executes the discovered input diagnostic/reset command path in emulator memory only.

### `smc_fw_catalog.py`

Runs the firmware's own key-catalog enumeration routine in isolated memory and emits the 2265-entry metadata catalog.

### `smc_fw_inspect.py`, `smc_fw_refs.py`

Small Capstone utilities used for range disassembly, immediate/call/reference searches and data-reference tracing. Set `SMC_FW=/path/to/image`.

### `extract_im4p.py`

Minimal extraction/decompression helper used while unpacking locally obtained Apple firmware containers. No Apple image is bundled here.

### `tm_inspect.py`

Helper used to inspect a local arm64e `thermalmonitord` image and Objective-C metadata cache. Set `THERMALMONITORD` and `THERMAL_OBJC` to local files.

## Experimental live probes

`experimental/` contains two narrowly constrained no-op/same-value SMC write-access probes preserved for completeness. They were rejected by the live controller. They are not required to reproduce the diagnosis. Read `SAFETY.md` before touching them.

## Dependencies

Python offline reverse-engineering helpers use `unicorn` and/or `capstone`; see the repository `requirements.txt`.
