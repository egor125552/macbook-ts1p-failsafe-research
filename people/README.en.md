# What happened to this MacBook, in plain language

This MacBook Air M4 can become extremely slow even while the processor is cool and macOS reports no ordinary thermal warning.

The investigation found that the problem is not ordinary CPU overheating. The Mac's SMC has stopped receiving a valid measurement from a required temperature input named `Ts1P`.

## What the machine does

In the normal path the SMC computes a package power limit of about **65 W**.

When the SMC sees a persistent fault on `Ts1P`, its built-in safety policy replaces that normal limit with a fixed **2 W** fail-safe. A separate utility limit changes from 30 W to 2.5 W.

macOS then receives the 2 W value as a thermal budget. Under real CPU load the machine cannot remain within that tiny budget, so the scheduler progressively stops recommending performance cores. On the investigated machine the mask was observed changing:

`1023 → 511 → 383 → 127 → 63`

At `63`, only the six efficiency cores remain in the recommended set. The result is severe slowdown in VoiceOver, application launch, compilation and other demanding work.

## Why it can look normal at idle

Even while the fail-safe `xPPT = 2 W` is active, the scheduler mask can return to `1023` at idle. A quick no-load test can therefore miss the problem completely.

## Why this is more than a zero-temperature guess

The same Ts1P key previously reported changing, plausible temperatures, roughly 18–31 °C in the available history. It now reports zero, along with a separate persistent SMC fault bit mapped to that input.

More importantly, the actual identified SMC firmware policy fragment was executed in an isolated copy. With the Ts1P fault present, it outputs 2 W / 2.5 W. When only that fault is cleared in the isolated memory, the output stays at 65 W / 30 W. The live Mac was not modified for this test.

## Is the battery the cause?

There is no evidence that the battery itself requests a 2 W limit. The SMC first computes the normal 65 W value and then applies the 2 W fail-safe because of the temperature-input fault.

Previous battery service may still be relevant indirectly. Disconnecting the battery fully removes power from always-on electronics, and opening the machine may disturb or reseat connectors. A marginal connection or a servicing controller that recovers after a true power cycle could therefore explain temporary recovery after repair.

The next repair question is why both Ts0P and Ts1P stopped delivering measurements: connector, flex, sensor power, shared sensor assembly, ADC, servicing controller, or another common path. The exact physical component is not yet proven.

## What to tell a repair technician

The short version is:

> Ts0P and Ts1P have stopped reporting temperature. Ts1P has a persistent SMC fault. The SMC still computes a normal 65 W package limit but changes the final xPPT value to 2 W because of that fault. Diagnose the missing Ts0P/Ts1P data path rather than assuming CPU overheating or replacing the battery again.

A useful controlled service test is to record Ts0P, Ts1P, SEB0 and xPPT; disconnect the same battery without disturbing other connectors; reconnect it; and immediately repeat the readings. Recovery from power removal alone would point toward a servicing controller. Recovery only after reseating a specific connection would point toward that physical path.

## What is still unknown

This repository does not claim a proven physical location for Ts1P on J713AP. Sensor names from older Macs are not enough to establish that.

No safe live software fix has been established. The goal is to restore the genuine temperature measurement, not to disable thermal protection.
