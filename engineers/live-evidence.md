# Live and historical evidence

## Current SMC state

Repeated reads through the ordinary AppleSMC user-client path returned successful driver and SMC result codes for the keys below.

| Key | Current value | Interpretation used here |
|---|---:|---|
| `Ts0P` | `0 °C` | adjacent temperature input currently not producing a valid reading |
| `Ts1P` | `0 °C` | required temperature input currently not producing a valid reading |
| `SES0` | `0x00001800` | current input-error bits 11 and 12 |
| `SEB0` | `0x00001000` | persistent input-error bit 12 |
| `SEB1…SEB7` | `0` | no other persistent bits in the checked exported words |
| `voPp` | `65 W` | normal pre-fault package limit computed by SMC |
| `voUp` | `30 W` | normal pre-fault utility limit |
| `xPPT` | `2 W` | final package limit after fail-safe policy |
| `xUPT` | `2.5 W` | final utility limit after fail-safe policy |
| `SFBN` | `0x12` | fail-safe state bits consistent with package/utility fallback |
| `SFBS` | `0x12` | same observed fail-safe bits |

The exact live transcript used for the public snapshot is stored in `data/live-snapshot-2026-10-13.txt`.

## Historical Ts0P / Ts1P values

The complete extracted series is `data/ts0p-ts1p-history.csv` with **900 measurements** from the available PowerLog databases.

Ranges summarized from the working analysis:

| Date | Ts1P | Ts0P |
|---|---:|---:|
| 2026-10-04 | 17.875–30.375 °C | 18.75–31.3125 °C |
| 2026-10-05 | 23.375–30.75 °C | 24.3125–31.6875 °C |
| 2026-10-06 | 23.9375–31.0625 °C | 25–31.875 °C |
| 2026-10-08 | 22.8125–31.375 °C | 23.8125–32.3125 °C |
| 2026-10-13 checked records | 0 °C | 0 °C |

The important point is not the exact historical temperature range. It is that both keys previously changed over time and therefore were active measurements on this Mac.

## Historical xPPT / xUPT values

The complete public series is `data/xppt-xupt-history.csv` with **879 measurements**.

Per-database summary:

| Date/database | Samples | xPPT min | xPPT max | xPPT exactly 2 W | xPPT > 10 W |
|---|---:|---:|---:|---:|---:|
| Oct 4 | 241 | ~2.000001 | 65 | 0 | 191 |
| Oct 5 | 206 | 2.3018 | 65 | 0 | 180 |
| Oct 6 | 245 | 4.0533 | 65 | 0 | 233 |
| Oct 8 | 152 | 2.3018 | 65 | 0 | 146 |
| Oct 13 current DB at analysis time | 35 | 2.0 | 65 | 32 | 2 |

On Oct 13 the database still contained brief high-limit records around 07:56 and 08:01 local UTC+03 time; by approximately 08:11 the recorded value was again 2 W and remained overwhelmingly pinned there in the sampled records.

The presence of occasional low xPPT values on earlier days is important: `xPPT ≈ 2 W` by itself is not enough to diagnose this fault. The abnormal condition is the persistent combination of failed Ts0P/Ts1P data, the Ts1P persistent fault bit, and the SMC fail-safe behavior.

## Clean scheduler-mask transition

A controlled trace produced this sequence:

```text
1023
511
383
127
63
127
383
511
383
511
383
511
1023
```

The exact timestamped sequence is in `data/scheduler-mask-transition.txt`.

An earlier experiment that appeared to leave mask 63 after load was invalid because four `yes` processes remained alive after a shell cleanup error. Those processes were identified and killed, after which the mask recovered. That invalid result is not used as evidence anywhere in this repository.

## PackageLimiter target and input

Ktrace event `0x3285005c` showed a 2.000 W target throughout the relevant window.

At scheduler mask 63, package input power had often already fallen below the target after throttling. In the analyzed records, median input was approximately 1.442 W, with values roughly spanning 1.334–2.652 W in the cited sample.

That observation explains why looking only at instantaneous package power can be confusing: the limiter has already changed scheduler behavior, so the post-throttle input can be below the target while the control state is still restrictive.

## CPU-average control effort

Approximate medians correlated by mask:

| mask | effort |
|---:|---:|
| 1023 | 0.171 |
| 511 | 0.154 |
| 383 | 0.117 |
| 127 | 0.093 |
| 63 | 0.022 |

The identified P-core removal threshold is around 0.1, matching the observed transition into reduced masks.

## Thermal state that did *not* explain the problem

During the broader investigation:

- ordinary thermal warnings were absent;
- previously observed temperatures were around 24–30 °C during symptomatic periods;
- brownout risk was 0;
- sampled local CPU PPT / hardware-thermal / external trigger channels did not show the expected direct hot-CPU explanation;
- global `THROTTLE_TRIG0/1` appeared in both healthy-mask and unhealthy-mask states and therefore did not discriminate the fault;
- PMC CLPC/DCS floors were at minimum and the observed DCS ceiling was maximum.

These negative observations are supporting context. The positive causal proof comes from the SMC input fault and isolated fail-safe replay, not from absence of other warnings.
