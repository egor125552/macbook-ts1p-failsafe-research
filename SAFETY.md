# Safety and scope

This repository is intended for diagnosis and research of a thermal-sensor fail-safe. It is **not** a guide to disabling thermal protection.

## Safe/read-only paths used here

- read SMC keys through the ordinary AppleSMC user client;
- read PowerLog databases in SQLite read-only mode;
- read `kern.sched_recommended_cores`;
- analyze legally obtained binaries offline;
- replay isolated firmware code in Unicorn memory;
- inspect already captured trace data.

## Actions intentionally not used as a fix

- kernel patching;
- SIP bypass;
- forced P-core enablement against an active hardware fault;
- disabling all thermal protections;
- overriding a missing temperature with a fabricated value;
- permanent NVRAM modifications;
- distributing privileged entitlement workarounds.

## Experimental write probes in `tools/experimental/`

For completeness, this repository preserves two constrained probes from the investigation. They were written specifically to avoid clearing faults or substituting sensor values:

- one attempts to write `SEB0`'s already-read bytes back unchanged;
- one attempts only all-zero/no-op writes to already-zero diagnostic selectors.

The live SMC rejected these operations with internal result 134. They are not needed for diagnosis, and users should prefer the read-only tooling.

## Why a 2 W override is the wrong repair target

The 2 W budget is a protective consequence. The root failure established here is loss of a required temperature measurement. Bypassing the budget without restoring the measurement removes a safety response while leaving the underlying fault intact.

A real repair should restore a trustworthy Ts1P measurement and verify that the persistent fault clears.
