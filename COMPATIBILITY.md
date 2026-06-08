# Compatibility matrix

| Technique | Chrome | Firefox | Edge | Safari | Notes |
|---|---|---|---|---|---|
| Filter lists (uBlock/AdGuard) | ✅ | ✅ | ✅ | ⚠️ | Safari via AdGuard for Safari; MV3 limits some rules on Chrome |
| User-agent override | ✅ (ext/CDP) | ✅ (`general.useragent.override`) | ✅ | ⚠️ | also override Client Hints on Chromium |
| Client Hints (Sec-CH-UA) | ✅ | n/a | ✅ | n/a | must match UA or you stand out |
| Geolocation spoof | ✅ (DevTools/ext) | ✅ (ext) | ✅ | ⚠️ | pair with timezone + locale |
| Timezone spoof | ✅ | ✅ (RFP) | ✅ | ⚠️ | Firefox `resistFingerprinting` forces UTC |
| Canvas/WebGL noise | ✅ (ext) | ✅ (RFP) | ✅ | ⚠️ | over-randomizing is itself a signal |
| Session containers | ⚠️ (profiles) | ✅ (native) | ⚠️ | ❌ | Firefox is strongest here |

Legend: ✅ supported · ⚠️ partial / via extension · ❌ not really · n/a not applicable.

**Golden rule:** internal consistency beats exotic values. A boring, *coherent* fingerprint hides better than a rare, contradictory one.
