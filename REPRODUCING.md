# Reproducing the research

The reproduction path is deliberately split into **read-only live measurements** and **offline binary analysis**.

Do not begin by trying to override thermal protections. The central result can be checked without changing the machine's power policy.

## 1. Build the read-only SMC helper

On macOS with the command-line developer tools:

```sh
clang -O2 -Wall -Wextra tools/read_smc_status.c -framework IOKit -framework CoreFoundation -o read_smc_status
```

Read the keys used by this case:

```sh
./read_smc_status Ts0P Ts1P SES0 SEB0 voPp voUp xPPT xUPT SFBN SFBS
```

On the investigated faulted machine the key pattern was:

```text
Ts0P 0
Ts1P 0
SES0 0x1800
SEB0 0x1000
voPp 65
voUp 30
xPPT 2
xUPT 2.5
```

Do not diagnose another machine solely because one numerical value happens to match. Compare fault flags and history as well.

## 2. Observe scheduler recommendation state

Read:

```sh
sysctl -n kern.sched_recommended_cores
```

For the 10-core M4 in this case:

```text
1023 = all ten low bits set
63   = low six bits set; only the six E-cores remain recommended
```

A full mask at idle does not clear the diagnosis. The faulted machine can return to 1023 while xPPT remains 2 W.

## 3. Extract PowerLog history

`tools/powerlog_extract.py` reads SMC key series from PowerLog SQLite databases in read-only mode. Exact table availability varies by OS version.

Example:

```sh
python3 tools/powerlog_extract.py \
  /var/db/powerlog/Library/BatteryLife/CurrentPowerlog.PLSQL \
  --keys Ts0P Ts1P xPPT xUPT \
  --output current-powerlog.csv
```

The already extracted data used by this report are included in `data/` so binary/system database access is not required to review the result.

## 4. Get the exact official Apple restore image

The repository does **not** mirror Apple firmware, but it pins the exact official Apple restore image used by this case so reproduction does not depend on hunting for a matching build.

For `Mac16,12` / `J713AP` / macOS 27.0 build `26A428`:

```sh
python3 tools/fetch_official_restore.py --download ./downloads
```

The helper downloads directly from `updates.cdn-apple.com`, supports resuming a partial `.part` file, checks the exact byte size, and refuses the image unless SHA-256 matches:

```text
file: UniversalMac_27.0_26A428_Restore.ipsw
size: 26626436228 bytes
SHA-256: 2a5d3c695d501022b7fad9adaffcf2627bcb867d993fb5662dcd41bac99a2836
```

To print the pinned Apple URL without downloading 26.6 GB:

```sh
python3 tools/fetch_official_restore.py --url-only
```

To verify an IPSW you already have:

```sh
python3 tools/fetch_official_restore.py --verify /path/to/UniversalMac_27.0_26A428_Restore.ipsw
```

The IPSW is the Apple restore container, not the final flat SMC image consumed by the emulator. After extracting the matching SMC payload locally, verify:

```text
name: AppleSMCFirmware_H16_4-7372.1.3.j713.REL
SHA-256: 010387bee26ac2937f2b835a9b54c1bde251334cac8ed23b12080d71bd8623fa
```

`tools/extract_im4p.py` is included for the IM4P/decompression step used during the investigation. Extraction details can vary with Apple restore-container layout, so always verify the final SMC SHA-256 before using build-specific offsets.

## 5. Offline SMC firmware replay

Install Python dependency:

```sh
python3 -m pip install unicorn
```

Run:

```sh
python3 tools/smc_failsafe_replay.py \
  --firmware /path/to/your/llb_nested_joined.bin
```

The script executes only an isolated memory copy. It does not open AppleSMC.

Expected qualitative result for the supplied case fixture:

```text
fault present  → package 2.0 W, utility 2.5 W
Ts1P cleared   → package 65 W, utility 30 W
```

See `data/smc-failsafe-replay.json` for the recorded result.

## 6. Fault-mask decoder

The small independent decoder can be tested without macOS:

```sh
python3 tools/fault_decode.py --mask 0x1000
python3 tools/fault_decode.py --mask 0x1800
```

Expected bit sets:

```text
0x1000 → [12]
0x1800 → [11, 12]
```

## 7. Raw trace evidence

The public trace files in `data/traces/` were captured from the investigated machine. They contain kernel trace rows and scheduler-mask timing used to validate the CLPC limiter chain.

The debug IDs are documented in `engineers/ppm-clpc.md` and `engineers/offsets-j713.md`.

Kernel tracing often requires elevated privileges and may differ by macOS release. The repository does not require a reader to reproduce kernel tracing in order to inspect the included evidence.

## 8. Binary-level verification

For researchers repeating static analysis on the same build:

- use a locally obtained matching kernelcache and thermalmonitord;
- use the address list only as an anchor;
- verify each function/table semantically before relying on an address;
- do not redistribute Apple binaries as part of an issue report or pull request.

The most important cross-check is the direction of causality: the SMC firmware itself must select the 2 W fallback when the required input is faulted. Merely finding a 2000 value later in PPM is not enough.

## Tests shipped with this repository

Run:

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile tools/*.py
```

On macOS, additionally syntax-check the C reader:

```sh
clang -fsyntax-only -Wall -Wextra tools/read_smc_status.c -framework IOKit -framework CoreFoundation
```

The tests intentionally use small fixtures and do not require Apple firmware.
