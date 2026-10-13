# Third-party and proprietary material

## Apple software

This repository documents behavior observed while analyzing Apple software and firmware, but does not redistribute Apple firmware, kernelcache, `thermalmonitord`, or wholesale disassembly.

Names, symbols, four-character SMC keys and small factual offset/value references are provided for interoperability, diagnosis and reproducibility.

## External projects and prior observations

Useful independent context found during the investigation includes:

- Asahi Linux SMC documentation: https://asahilinux.org/docs/hw/soc/smc/
- iFixit case with an Apple Silicon Mac showing Ts0P/Ts1P zero and severe throttling: https://www.ifixit.com/Answers/View/928482/Fans+run+at+100%25,+cpu+under+clocked,+even+though+temps+are+low
- iFixit historical SMC/sensor-cable repair discussion: https://www.ifixit.com/Answers/View/363003/SMC+Problem+Reference+Code+PFM+006
- `iSMC` community sensor-name mappings: https://github.com/dkorunic/iSMC
- Apple/XNU scheduler source and tests where relevant: https://github.com/apple-oss-distributions/xnu
- An external experimental ApplePassthroughPPM research gist discovered while evaluating whether a temporary macOS-side budget override existed: https://gist.github.com/andrew-kramer-inno/f7e8449b521b7435e91c92ae6b3ae6d8

Third-party source code from these projects is **not copied into this repository**. Follow the license at the original source.

## “First” claim

Public searches found earlier reports of the symptom and earlier reverse engineering of individual subsystems. This repository therefore does not claim to be the first discovery of Ts0P/Ts1P-related throttling.

What appears unusual is the depth of the documented end-to-end chain on this J713AP case: required SMC input fault → firmware 2 W fail-safe → PTD/PPM 2000 mW → CLPC SLOWTEMP → P-core removal. If earlier public work has already established the same complete chain, contributions and references are welcome.
