# Engineering index

This section documents the evidence from the lowest identified SMC policy input through macOS power management and scheduler behavior.

## System under test

- MacBook Air M4
- Model identifier: `Mac16,12`
- SoC: Apple M4 / T8132
- CPU topology: 6 E-cores + 4 P-cores
- Hardware target: `J713`
- MobileGestalt `HWModelStr`: `J713AP`
- macOS 27.0, build `26A428`

## Established chain

```text
Ts1P measurement path fails
        ↓
SMC input 12 persistent fault
SEB0 bit 12 = 0x1000
        ↓
SMC required-input policy detects fault
        ↓
normal voPp 65 W → fail-safe xPPT 2.0 W
normal voUp 30 W → fail-safe xUPT 2.5 W
        ↓
PTD C01 / C02
        ↓
PPM DetailedThermalBudget
package: type 2, source 0, 2000 mW
        ↓
CLPC reason mapping → reason code 1
        ↓
CLPC::setSlowThermalBudget
DVF reason 0x3200000d = SLOWTEMP
        ↓
PackageLimiter AverageThermal target = 2.000 W
        ↓
CPULimiter effort falls below P-core removal threshold
        ↓
SchedulerInterface removes P-cores from recommended mask
1023 → 511 → 383 → 127 → 63
```

## Evidence layers

1. [`live-evidence.md`](live-evidence.md): direct SMC values, historical PowerLog values and clean scheduler transition measurements.
2. [`smc-firmware.md`](smc-firmware.md): key catalog mapping, required-input policy, fixed 2/2.5 W fail-safe and isolated replay.
3. [`ppm-clpc.md`](ppm-clpc.md): transport from PTD C01/C02 through PPM into CLPC SLOWTEMP and the CPU limiter.
4. [`offsets-j713.md`](offsets-j713.md): compact firmware/kernel offsets, symbols and event IDs used in this specific build.
5. [`repair-diagnostics.md`](repair-diagnostics.md): what the evidence implies for board-level/service diagnosis.
6. [`negative-results.md`](negative-results.md): experiments that did not explain or fix the root fault.

## Confidence labels used in this repository

**Proven:** directly observed and/or reproduced with a controlled causal experiment.

**Strongly supported:** multiple independent observations agree, but one link has not been directly manipulated.

**Hypothesis:** plausible interpretation that still needs a discriminating experiment.

The physical identity and location of Ts1P on J713AP is intentionally kept in the hypothesis category.

## Important terminology correction

An earlier stage of the investigation called the 2000 mW record “DetailedThermalBudget type 1.” That was incorrect. Live PPM records show **type 2**. A separate mapping then converts that entry to **CLPC reason code 1**, which selects the slow-thermal path. Budget type, reason code and time scale are different fields and must not be conflated.

## Reproducibility boundary

This repository redistributes only original research code, measurements and descriptions. It does not include Apple firmware, kernelcache, `thermalmonitord`, or wholesale disassembly. To reproduce the binary-level work, use legally obtained local copies matching the documented hashes/builds.
