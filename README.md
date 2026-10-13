# Apple Silicon Ts1P fail-safe research

A reproducible reverse-engineering case study of an Apple Silicon Mac entering an extreme low-power state after losing a required SMC temperature input.

**Test machine:** MacBook Air M4, `Mac16,12`, hardware target `J713`, MobileGestalt `J713AP`, macOS 27.0 build `26A428`.

## Result in one sentence

On the affected machine, the SMC has a persistent fault for required temperature input **Ts1P**. The matching SMC firmware policy replaces the normal package limit of **65 W** with a fixed **2 W** fail-safe. That value is forwarded through PTD/PPM as a **2000 mW DetailedThermalBudget**, reaches CLPC as **SLOWTEMP**, and under load causes performance cores to be removed from `kern.sched_recommended_cores` until the mask can reach `63`.

This repository contains the measurements, reverse-engineering notes, original analysis tools and isolated firmware-policy replay used to establish that chain.

> This is an investigation, not a thermal-protection bypass. The physical reason that Ts0P/Ts1P stopped producing valid measurements on this particular J713AP is **not yet established**.

## Start here

- **Non-technical explanation:** [`people/README.en.md`](people/README.en.md)
- **Объяснение по-русски:** [`people/README.ru.md`](people/README.ru.md)
- **Engineering index:** [`engineers/README.md`](engineers/README.md)
- **Full causal chain:** [`engineers/causal-chain.md`](engineers/causal-chain.md)
- **SMC firmware findings:** [`engineers/smc-firmware.md`](engineers/smc-firmware.md)
- **PTD / PPM / CLPC findings:** [`engineers/ppm-clpc.md`](engineers/ppm-clpc.md)
- **Repair-oriented diagnostics:** [`engineers/repair-diagnostics.md`](engineers/repair-diagnostics.md)
- **Negative results and red herrings:** [`engineers/negative-results.md`](engineers/negative-results.md)
- **Case/service timeline:** [`CASE_TIMELINE.md`](CASE_TIMELINE.md)
- **Reproduction guide:** [`REPRODUCING.md`](REPRODUCING.md)
- **Safety notes:** [`SAFETY.md`](SAFETY.md)

## What is proven

1. `Ts1P` previously returned changing, plausible temperatures and now reads `0 °C` on the affected machine.
2. `SEB0 = 0x00001000` is the persistent fault bit corresponding to SMC input 12, mapped to `Ts1P` in the matching firmware key catalog.
3. The SMC still computes normal pre-fault limits `voPp = 65 W` and `voUp = 30 W`, but publishes post-fault values `xPPT = 2 W` and `xUPT = 2.5 W`.
4. Running the identified SMC policy fragment in an **isolated copy** of the matching firmware gives 2/2.5 W with the Ts1P fault set and 65/30 W when only that fault is cleared.
5. `xPPT = 2.0 W` is transported as PTD C01 and becomes a PPM `DetailedThermalBudget` of 2000 mW, type 2, source 0.
6. The PPM entry maps to CLPC reason code 1, which selects the slow-thermal path. Live CLPC traces report reason low byte `0x0d` (`SLOWTEMP`) while the package target is 2.000 W.
7. During a clean load experiment the scheduler recommendation mask was observed moving `1023 → 511 → 383 → 127 → 63`, removing all four P-cores from the recommended set.

## What is not proven

- The exact physical location of `Ts1P` on J713AP.
- Whether the failed part is a sensor, connector, flex, power rail, ADC, servicing controller, or another shared element.
- Whether Ts0P and Ts1P share the same physical device on this model.
- A safe software fix for a live machine with the hardware/data-path fault present.

The fact that both Ts0P and Ts1P currently read zero makes a shared path/controller a reasonable repair hypothesis, but it remains a hypothesis.

## Key live snapshot

| Key / state | Observed value |
|---|---:|
| `Ts0P` | `0 °C` |
| `Ts1P` | `0 °C` |
| `SES0` | `0x00001800` |
| `SEB0` | `0x00001000` |
| `voPp` | `65 W` |
| `voUp` | `30 W` |
| `xPPT` | `2 W` |
| `xUPT` | `2.5 W` |
| `SFBN`, `SFBS` | `0x00000012` |
| idle `kern.sched_recommended_cores` | can still be `1023` |
| severe loaded mask | `63` |

## Repository contents

`data/` contains full measurement series that can be redistributed: 879 xPPT/xUPT records and 900 Ts0P/Ts1P records from the available PowerLog databases, plus the isolated replay result and selected scheduler/trace evidence.

`tools/` contains code written during this investigation. Apple firmware, kernelcache, `thermalmonitord`, and other Apple binaries are **not** included. Bring legally obtained local copies if you want to reproduce binary analysis.

## Firmware identity

The SMC image used for the isolated analysis was identified as:

`AppleSMCFirmware_H16_4-7372.1.3.j713.REL`

SHA-256:

`010387bee26ac2937f2b835a9b54c1bde251334cac8ed23b12080d71bd8623fa`

The binary itself is intentionally not redistributed here.

## License

Original source code and documentation in this repository are released under the MIT License. That license does not apply to Apple software, firmware, third-party projects, or external source material referenced by the research. See [`THIRD_PARTY.md`](THIRD_PARTY.md).
