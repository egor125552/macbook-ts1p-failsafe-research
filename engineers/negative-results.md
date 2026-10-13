# Negative results, corrections and red herrings

A useful public reverse-engineering report should preserve failed hypotheses so other researchers do not have to rediscover them.

## 129000 in PowerLog is not the new failure

Historical CPMS client records contained values such as:

```text
clpc_100ms = 1000000
clpc_1sec  = 129000
clpc_Insta = 129000
requested clpc_100ms = 128001
```

The 129000 values also existed on earlier days when the machine was not in the persistent 2 W failure state. They belong to a different layer/units and must not be equated with the 2.000 W CLPC thermal target.

## `PackageLowPowerTarget = 4000` does not become 2000

The J713AP thermalmonitord configuration includes `PackageLowPowerTarget = 4000.0`. Reverse engineering `MitigationController::setPackageLowPowerTarget` showed that it becomes a 4 W low-power-mode target; no divide-by-two step exists.

A live Low Power Mode experiment changed that path independently while the 2000 mW thermal-budget entry persisted.

## THROTTLE_TRIG0 / THROTTLE_TRIG1 are not discriminating causes

These global triggers were active in both full-mask and reduced-mask observations. Their presence therefore did not explain why the machine specifically entered mask 63.

## No ordinary hot-CPU evidence

The problem can occur on a cold machine, including previously observed temperatures around the mid-20s °C, without the ordinary macOS thermal warning expected from actual overheating. This observation alone did not prove the root cause, but it correctly pushed the investigation toward lower-level policy/fault handling.

## Lifetime Servo remains context, not the demonstrated trigger

ApplePMPv2 exposed `lts-ctrl-enbl-thrtl=1`, and thermalmonitord contains LTS configuration/state handling. However, published LTS fields inspected across selected healthy/bad samples did not provide the state transition needed to explain this failure.

Disabling LTS was not used as a solution and should not be used to mask a missing required temperature input.

## CLPC reset is symptom reset, not root repair

Static analysis established that wake re-enables CLPC through a path that calls `CLPC::reset()`. Sleep/wake can restore the scheduler mask, but the external bad budget can be delivered again.

This means CLPC's internal state can amplify/release the visible symptom, while the root 2 W request still comes from above/below through the SMC/PPM path.

## Invalid old `yes` result

One early load test appeared to show that mask 63 remained after load. That result was invalid.

Four `yes` processes remained alive because a zsh PID cleanup expression was wrong. After those PIDs were actually killed, the mask recovered to 1023. A later script used a proper zsh array and `trap cleanup`.

No conclusion in the final causal chain relies on the contaminated test.

## Old SMC reader produced misleading zeros for absent keys

An early helper checked only the IOKit return code and ignored the SMC's internal result byte. An absent key could therefore be displayed as zero even when the controller had returned an error (for example result 132).

The corrected reader validates both the kernel call and the SMC result and handles larger key payloads. The current Ts0P/Ts1P zero readings are successful key reads, not this old parsing bug.

## Live SMC write attempts did not clear the fault

A deliberately constrained same-value write probe for `SEB0` sent the already-read bytes back unchanged. IOKit accepted the call path, but the SMC returned internal result 134 and the value remained unchanged.

`MSFL` / `MSFN` diagnostic keys were likewise not accessible for the identified reset operation through the ordinary interface. The reset behavior was tested only in isolated firmware memory.

## Private PPM interface is not an ordinary-admin workaround

Opening `ApplePPM`, `ApplePassthroughPPM` and `ApplePPMCPMS` user clients across tested types was rejected with `0xe00002c7` in the research process. Public examples that modify detailed budgets rely on execution contexts with additional entitlements.

Even if such a budget override were available, changing the accepted macOS budget would not restore the missing Ts1P measurement.

## `UseOverrideThermalBudgets` is not a fix

The property was shown to suppress application of incoming DetailedThermalBudgets while allowing lower-layer control-effort updates. With 2 W already stored, enabling it can retain the bad budget rather than remove the sensor fault.

## DFU Revive did not solve the observed recurring problem

A prior DFU Revive did not prevent recurrence. This fits the current finding that the SMC is reacting to a missing required measurement rather than to a simple corrupt macOS preference.

## Physical sensor location remains unproven

External projects and older Mac sensor naming provide hints about `Ts0P/Ts1P`, but those hints are not a board-level mapping for J713AP. This repository intentionally avoids promoting such a hint into a fact.
