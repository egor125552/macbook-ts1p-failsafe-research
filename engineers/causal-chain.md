# Full causal chain

This document states each link in the failure chain and the evidence behind it.

## 1. A required SMC temperature input stopped producing a valid measurement

Current live values on the affected J713AP:

```text
Ts0P = 0.0
Ts1P = 0.0
SES0 = 0x00001800
SEB0 = 0x00001000
```

Historical PowerLog records show Ts0P/Ts1P previously returning plausible, changing temperatures. The full series is in `data/ts0p-ts1p-history.csv`.

The persistent fault mask `SEB0 = 0x1000` identifies input bit 12. The matching SMC firmware catalog maps descriptor/input 12 to `Ts1P`.

**Status: proven.**

## 2. The SMC fail-safe converts the normal package limit into 2 W

Live readings:

```text
voPp = 65.0 W
voUp = 30.0 W
xPPT = 2.0 W
xUPT = 2.5 W
SFBN = 0x12
SFBS = 0x12
```

The matching SMC firmware contains a required-input policy. Input 12 appears in both package and utility required-input lists. If a required input is faulted, the policy loads fixed constants 2.0 and 2.5 W instead of the pre-fault `voPp` / `voUp` values.

The identified policy fragment was executed in an isolated Unicorn memory image using the observed live fault masks. With Ts1P faulted it produced 2.0/2.5 W. Clearing only input 12's fault flag in the isolated copy produced 65/30 W.

No live SMC key or protection state was modified by this experiment.

**Status: proven causal link.**

## 3. xPPT is transported into macOS as a 2000 mW detailed thermal budget

The SMC result path sends:

```text
xPPT → PTD packet C01
xUPT → PTD packet C02
```

The macOS PTD parser converts the floating-point watt value to milliwatts with the equivalent of:

```text
uint(value_watts * 1000 + 0.5)
```

Live PPM tracing identifies:

```text
C01 → DetailedThermalBudget type 2, source 0, 2000 mW
C02 → DetailedThermalBudget type 2, source utility_, 2500 mW
C10 → separate low-power-mode budget source lpwrmode
```

The 2000 mW entry persists independently of ordinary macOS Low Power Mode. A controlled Low Power Mode experiment changed its own `lpwrmode` entry and the AppleCLPC low-power target, while the 2000 mW record remained.

**Status: proven transport/value mapping; C01/xPPT association is supported by matching code path and values.**

## 4. PPM maps the 2000 mW entry to CLPC slow thermal

The PPM policy path includes:

```text
ApplePPMPolicyCPMS::setDetailedThermalPowerBudget
ApplePPMPolicyCPMS::setDetailedThermalPowerBudgets
ApplePPMCPMS::updateTimestampsTracesAndShimBudgets
ApplePPMCPMS::setDetailedThermalPowerBudgetsGated
ApplePPMCPMS::handleLowerLayerUpdate(DetailedThermalBudgets*, float*)
ApplePPMCPMS::smcTargetsUpdateEventHandler
```

A mapping table converts the “type 2, source 0” budget into CLPC reason code 1. `AppleCLPC::setPowerBudgets` handles this reason through `CLPC::setSlowThermalBudget`.

Live DVF trace records use packed reason `0x3200000d`; the low byte `0x0d` corresponds to `SLOWTEMP`.

**Status: proven by static routing plus live trace reason.**

## 5. CLPC runs a package limiter against a 2.000 W target

The relevant observed chain is:

```text
CLPC::samplePowerAndThermals
  → PackageLimiter::run
  → CPULimiter::run
  → SchedulerInterface
```

Ktrace event `0x3285005c` reports a constant target of 2.000 W during the failure experiment.

At the most severe scheduler state (mask 63), the measured package input was often already below 2 W after throttling; its median in the analyzed sample was about 1.442 W. The CPU-average control effort nevertheless remained very low because of the regulator state/release dynamics.

**Status: proven.**

## 6. Low control effort causes P-core removal

The CPU limiter's P-core removal threshold was identified near `0.1` (`0x3dcccccd` as float).

Observed median CPU-average effort by scheduler mask:

| Mask | Approx. median effort |
|---:|---:|
| 1023 | 0.171 |
| 511 | 0.154 |
| 383 | 0.117 |
| 127 | 0.093 |
| 63 | 0.022 |

The clean scheduler transition trace contains:

```text
1023
511
383
127
63
...
127
383
511
...
1023
```

On this 10-core machine, mask 63 corresponds to the six low-order efficiency cores remaining recommended, with all four performance cores excluded.

**Status: proven by static threshold and live correlated trace.**

## Why a cold machine can report SLOWTEMP

`SLOWTEMP` in this chain does not mean the CPU die itself must be hot. It is the CLPC reason used for the slow-thermal budget delivered from the lower thermal/power-management path. Here that path originates from an SMC fail-safe caused by loss of a required temperature input.

That resolves the apparent contradiction between low physical temperatures and aggressive “thermal” throttling.

## Why idle can be misleading

`kern.sched_recommended_cores` can return to 1023 while the SMC still exposes `xPPT = 2 W`. The limit becomes visibly destructive when sustained work demands more than the fail-safe budget.

Therefore, a healthy-looking idle scheduler mask does not demonstrate that the underlying fault has cleared.
