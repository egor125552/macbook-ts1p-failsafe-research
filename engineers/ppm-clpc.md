# PTD, PPM and CLPC path

This document covers the macOS side after the SMC has already selected the 2.0 W package fail-safe.

## PTD packet mapping

The investigated path associates:

```text
C01 → package xPPT
C02 → utility xUPT
C10 → low-power-mode path
```

The PTD parser converts a floating-point value expressed in watts to an integer budget in milliwatts using the equivalent of:

```c
(uint32_t)(watts * 1000.0 + 0.5)
```

Therefore:

```text
2.0 W  → 2000 mW
2.5 W  → 2500 mW
65 W   → 65000 mW
```

## Live DetailedThermalBudget records

Observed records include:

| Origin | Budget type | Source/details | Value |
|---|---:|---|---:|
| C01 / package | 2 | 0 | 2000 mW |
| C02 / utility | 2 | `utility_` | 2500 mW |
| C10 / low-power mode | 2 | `lpwrmode` | 65000 mW in normal mode; changes independently |

A previous draft incorrectly called the package record “type 1.” The live trace corrected this to **type 2**.

## Why 4000 in thermalmonitord is not the source of 2000

The J713AP `thermalmonitord` product configuration contains:

```text
powerSaveParams.PackageLowPowerTarget = 4000.0
powerZoneParams.usesPackageControl = true
```

`MitigationController::setPackageLowPowerTarget` around `0x10000186c` uses 4000 while power-save mode is active and otherwise uses 65000. The method scales milliwatts to watts for the AppleCLPC property. It produces 4 W from 4000; there is no divide-by-two operation that would explain 2 W.

A controlled Low Power Mode toggle showed that its own AppleCLPC/PPM values changed and returned while the independent 2000 mW package thermal budget persisted. This removed the 4000→2000 hypothesis.

## PPM route

Relevant symbols / functions identified in the build include:

```text
ApplePPMPolicyCPMS::setDetailedThermalPowerBudget
ApplePPMPolicyCPMS::setDetailedThermalPowerBudgets
ApplePPMPolicyCPMS::copyDetailedThermalBudgetsResolved
ApplePPMCPMS::updateTimestampsTracesAndShimBudgets
ApplePPMCPMS::setDetailedThermalPowerBudgetsGated
ApplePPMCPMS::handleLowerLayerUpdate(DetailedThermalBudgets*, float*)
ApplePPMCPMS::smcTargetsUpdateEventHandler
```

The lower-layer update path is consistent with the PTD/SMC target delivery discovered above.

A mapping table near kernel virtual address `0xfffffe00076dbcf0` maps the PTD packet forms to DetailedThermalBudget entries.

A second table near `0xfffffe00076db2f8` maps the package entry `(type 2, source 0)` to **CLPC reason code 1**.

## AppleCLPC route

`AppleCLPC::setPowerBudgets` is near:

```text
0xfffffe0009f831fc
```

Reason code 1 selects `CLPC::setSlowThermalBudget`, near:

```text
0xfffffe0009f8dce0
```

The resulting DVF reason observed in ktrace is:

```text
0x3200000d
```

The low byte is `0x0d = 13`, identified as `SLOWTEMP`.

The selected PackageLimiter AverageThermal target is then 2.000 W.

## CLPC limiter path

The static/live path established during the investigation is:

```text
CLPC::samplePowerAndThermals
  → PackageLimiter::run
  → CPULimiter::run
  → SchedulerInterface
```

The package input consumed by the limiter is derived from PMGR energy-node counters through the `SystemThermalSample` aggregate-power field rather than from a direct die-temperature reading. That distinction matters: the 2 W **target** originates from the missing-temperature fail-safe, while the limiter **input** is measured/aggregated power.

## Important trace events

| Debug ID | Meaning used in analysis |
|---|---|
| `0x3285005c` | PackageLimiter 1 s PI state / target |
| `0x32850064` | CPU average limiter |
| `0x32850034` | DVFManager setPowerLimit reason |
| `0x32850048` | raw sample |
| `0x3284007c` | upper sampler event |
| `0x32840288` | per-energy-node event; normally disabled at observed debug level |
| `0x32850078` | selected target; disabled at observed debug level |
| `0x27f8....` | PPM event family used for budget transport analysis |

## P-core removal threshold

The static threshold associated with `power_cpu_limiter_rm_core` is approximately:

```text
0.1f
hex float 0x3dcccccd
```

Observed effort values cross this threshold as the scheduler mask contracts. See `causal-chain.md` and the trace data.

## CLPC reset and sleep/wake

Reverse engineering also established:

```text
CLPC::systemWake()
  → CLPC::enable(true)
  → T8132CLPC vtable slot +0x20
  → CLPC::reset()
```

Sleep/wake can therefore reset substantial CLPC state and temporarily restore a full scheduler mask. However, the external SMC/PPM budget can be delivered again, so this is not a root-cause repair.

## `UseOverrideThermalBudgets`

`UseOverrideThermalBudgets=1` prevents incoming lower-layer DetailedThermalBudgets from being applied through the normal policy update, while lower-layer control-effort updates continue. This is narrower than disabling all thermal protection.

It is not a fix here. With an already stored 2 W budget, freezing updates can simply freeze the bad budget. It was investigated only as a causal tool and is not recommended as a user workaround.
