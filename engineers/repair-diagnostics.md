# Repair-oriented diagnostics

This document translates the software evidence into useful service tests. It deliberately does not claim an unproven physical location for Ts1P on J713AP.

## Confirmed fault presented to the repair path

On the affected machine:

```text
Ts0P = 0 °C
Ts1P = 0 °C
SES0 = 0x1800
SEB0 = 0x1000
voPp = 65 W
xPPT = 2 W
```

The SMC firmware policy has been causally replayed: input-12/Ts1P fault causes the fixed 2 W package fallback.

Therefore, a repair should focus on **why the required temperature measurement is not reaching the SMC**, not on defeating the 2 W fallback.

## Highest-value first test

When the machine is currently faulted:

1. Record `Ts0P`, `Ts1P`, `SES0`, `SEB0`, `voPp`, `xPPT`.
2. Shut the machine down.
3. Physically disconnect the existing battery while avoiding disturbance to unrelated flexes/connectors as much as practical.
4. Allow a true removal of always-on power.
5. Reconnect the same battery.
6. Boot and immediately read the same SMC keys again before doing other repair work.

### Interpretation

If Ts0P/Ts1P recover after battery power removal alone, this strongly supports a servicing controller / ADC / always-on state problem that is not reset by an ordinary macOS restart.

If they do not recover from power removal but recover after reseating a specific connector or flex, that strongly supports a marginal physical path.

If they remain faulted until a sensor/assembly/board component is replaced, that localizes the failure further.

## Why battery replacement itself is not established as the cure

The failure first occurred before any repair. Previous battery service was followed by temporary recovery, once for only days and another time for months.

That history is consistent with several indirect effects of battery service:

- complete power removal from always-on electronics;
- mechanical reseating or movement of nearby connectors/flexes;
- altered mechanical pressure after reassembly;
- replacement of a part that happens to share a sensor path.

The current software evidence does **not** show the battery requesting a 2 W package limit. The SMC computes 65 W and then substitutes 2 W after the required-input fault.

## Why both Ts0P and Ts1P matter

The captured current-error word has bits 11 and 12 (`0x1800`), while the persistent captured fault word has bit 12 (`0x1000`). Both temperature keys currently read zero.

Two independent sensors can fail, but simultaneous loss raises the repair priority of any component shared by the two channels:

- common connector or flex;
- common sensor power/reference;
- shared ADC or MCU;
- common bus segment;
- common assembly.

This is a **hardware hypothesis**, not a proven topology map.

## Suggested service acceptance criteria

A repair should not be considered verified merely because the Mac feels fast at idle.

A useful success checklist is:

```text
Ts1P returns a plausible, changing temperature
Ts0P also returns a plausible changing value if the same path is repaired
SEB0 bit 12 is no longer persistent
xPPT is no longer fixed at 2 W because of this fault
short controlled CPU load no longer drives recommended-core mask to 63
no new sensor fault is created
```

The expected normal xPPT is not always 65 W at every instant; macOS/SMC has multiple legitimate power policies. The key diagnostic is removal of the Ts1P fault and disappearance of its fixed emergency fallback behavior.

## Read-only SMC helper

`tools/read_smc_status.c` can read the relevant keys through the ordinary AppleSMC interface. Example after compilation:

```sh
./read_smc_status Ts0P Ts1P SES0 SEB0 voPp voUp xPPT xUPT SFBN SFBS
```

For a service comparison, save output before and after each **single** physical intervention. Avoid changing three connectors at once if the goal is to localize the defect.

## Do not use these as repair proof

The following can temporarily change symptoms without repairing the missing sensor path:

- sleep/wake resetting CLPC state;
- idle scheduler mask returning to 1023;
- manually altering a power budget through privileged/private interfaces;
- freezing detailed thermal-budget updates;
- forcing P-cores back into service;
- replacing a battery without checking whether Ts0P/Ts1P themselves recovered.

The target of a real repair is the temperature-data path.
