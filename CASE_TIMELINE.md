# Case timeline

This is the symptom/service history relevant to interpreting the technical evidence. Some early dates were recalled as intervals rather than recorded timestamps, so they are intentionally described approximately.

## Before any repair

The first severe slowdown appeared roughly **four months after purchase**. This matters because it means later battery replacement cannot be the original cause of the failure.

Symptoms included very slow system/VoiceOver response and substantially slower boot. The machine could be cold and the issue was not explained by an ordinary thermal warning.

## First battery/service intervention

A battery replacement / full internal power disconnect was followed by an apparent recovery lasting only about **three days**, after which the severe slowdown returned.

At the time the Ts1P mechanism had not yet been identified, so no before/after Ts0P/Ts1P measurements were captured around that service event.

## Later intervention

After another service intervention, the machine remained apparently healthy for about **four months** before the same class of problem returned.

Again, this does not prove that the battery itself was causal. Service also causes a true removal of always-on power and mechanical movement/reseating of internal connections.

## Other attempted software recovery

A DFU Revive did not prevent the recurring failure. Battery replacement likewise did not permanently eliminate it.

Sleep/wake can transiently reset CLPC/scheduler state, but the bad thermal budget can be delivered again. Therefore a temporary performance recovery is not proof that the sensor/data-path fault has disappeared.

## October 2026 recorded history

PowerLog data available for October 4, 5, 6 and 8 shows Ts0P/Ts1P returning plausible, changing temperatures. On October 13, the checked current records show both at zero.

The current database also shows xPPT transitioning from records at 65 W early in the day to an overwhelmingly persistent 2 W state later in the captured period.

By the October 13 investigation, the live machine simultaneously showed:

```text
Ts0P = 0
Ts1P = 0
SES0 = 0x1800
SEB0 = 0x1000
voPp = 65 W
xPPT = 2 W
```

A public snapshot captured at 15:26 UTC+03 additionally showed:

```text
kern.sched_recommended_cores = 63
```

## What the service history suggests, but does not prove

The pattern “works for months, fails, recovers after machine is opened/power-removed, fails again” is compatible with either:

- a marginal shared physical path such as connector/flex/power/reference;
- an always-on servicing controller/ADC that recovers from a true power cycle;
- an intermittent sensor assembly or board-level fault.

The three-day recurrence after one service event argues against a simple fixed four-month software timer. The exact component remains an open hardware question.
