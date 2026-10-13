# J713 / build 26A428 reference offsets

These addresses are build- and image-specific research anchors, **not stable APIs**. Do not apply them to another OS build or SMC firmware without re-identification.

## SMC firmware `AppleSMCFirmware_H16_4-7372.1.3.j713.REL`

SHA-256:

`010387bee26ac2937f2b835a9b54c1bde251334cac8ed23b12080d71bd8623fa`

| Purpose | Offset / value |
|---|---|
| key-catalog enumeration routine | `0x2d0bc` |
| `hex_` read byte-order path | `0x2d338…0x2d360` |
| input descriptor array base used by replay | `0x840f0` |
| Ts1P / input 12 descriptor | `0x84270` |
| input value-pointer area | `0x7b910` |
| Ts1P mapped value | `0xa0e70` |
| persistent fault formation | about `0x3b4b4` |
| required-input fault test | about `0x3b448` |
| fault-mask packing | about `0x33c6c` |
| exported fault-mask array | `0x9ca18` |
| package required-input list | `0x89878`, 42 entries |
| utility required-input list | `0x87c80` |
| fixed fallback constants | `0x87130` |
| fail-safe policy fragment | `0x39b4c…0x39ba0` |
| xPPT/xUPT result area | around `0x87918` |
| final PTD send path | about `0x3a180` |
| diagnostic command callback used in isolated reset replay | about `0x2b0b4` |

## thermalmonitord arm64e image used during investigation

| Purpose | Address |
|---|---|
| startup function | about `0x100011114` |
| J713AP constant dictionary | `0x100080128` / file offset `0x80128` |
| `MitigationController::updatePowerSaveActive` | about `0x1000017ec` |
| `MitigationController::setPackageLowPowerTarget` | about `0x10000186c` |

Decoded J713AP product configuration contained:

```text
PackageLowPowerTarget = 4000.0
usesPackageControl = true
LTSUsesACSK = enabled
needsLTSStatePersistence = enabled
usesSMCSensorExchange = enabled
```

The 4000 value belongs to the Low Power Mode path and was shown not to explain the independent 2000 mW thermal budget.

## Kernel / AppleCLPC / ApplePPM anchors

The following addresses are from the kernelcache corresponding to the investigated system and are included only as reproducibility anchors.

| Symbol / purpose | Address |
|---|---|
| `AppleCLPC::setPowerBudgets` | about `0xfffffe0009f831fc` |
| `CLPC::setSlowThermalBudget` | about `0xfffffe0009f8dce0` |
| `CLPC::reset()` | about `0xfffffe0009f8c020` |
| `CPULimiter::reset(unsigned long long)` | about `0xfffffe0009f555b0` |
| `PackageLimiter::reset(unsigned long long)` | about `0xfffffe0009f597d4` |
| `DVFManager::reset(unsigned long long)` | about `0xfffffe0009f61a24` |
| `PreferenceManager::reset(...)` | about `0xfffffe0009f64f5c` |
| `SchedulerInterface::reset()` | about `0xfffffe0009f663ec` |
| PTD→DetailedThermalBudget mapping table | about `0xfffffe00076dbcf0` |
| DetailedThermalBudget→CLPC reason table | about `0xfffffe00076db2f8` |
| `ApplePPMPolicyCPMS::setDetailedThermalPowerBudget` | about `0xfffffe0009bfaf7c` |
| `ApplePPMPolicyCPMS::setDetailedThermalPowerBudgets` | about `0xfffffe0009bfb1ec` |
| `copyDetailedThermalBudgetsResolved` | about `0xfffffe0009bfd4a8` |
| `ApplePPMCPMS::updateTimestampsTracesAndShimBudgets` | about `0xfffffe0009c0e064` |
| `setDetailedThermalPowerBudgetsGated` | about `0xfffffe0009c0fe84` |
| `handleLowerLayerUpdate(DetailedThermalBudgets*,float*)` | about `0xfffffe0009c0b900` |
| caller `smcTargetsUpdateEventHandler` | about `0xfffffe0009c0b2b8` |

## ktrace IDs

| ID | Interpretation in this investigation |
|---|---|
| `0x3285005c` | PackageLimiter 1-second PI state / target |
| `0x32850064` | CPU average limiter |
| `0x32850034` | DVFManager power-limit reason |
| `0x32850048` | raw sample |
| `0x3284007c` | upper sampler |
| `0x32840288` | per-energy-node event, normally disabled |
| `0x32850078` | selected target, disabled at tested debug level |
| `0x27f80220`, `0x27f80224` | PPM detailed budget events used during routing analysis |

## Constants

```text
power_cpu_limiter_rm_core threshold ≈ 0.1f = 0x3dcccccd
DVF packed SLOWTEMP reason = 0x3200000d
SLOWTEMP low byte = 0x0d = 13
normal package value observed = 65 W
fail-safe package value = 2 W
normal utility value observed = 30 W
fail-safe utility value = 2.5 W
persistent Ts1P fault mask = SEB0 0x00001000
current Ts0P+Ts1P fault mask = SES0 0x00001800
```

## Address hygiene

If a future researcher uses another macOS build or firmware revision, re-derive every address from symbols, strings, data-flow and behavior. Matching a numeric address across builds by coincidence is not evidence.
