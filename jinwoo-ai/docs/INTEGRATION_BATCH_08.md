# Controlled Integration Batch 08 — Geospatial Visualisation Safety Intake

**Status:** the owner-requested [God's Eye View](https://github.com/bilawalsidhu/gods-eye-view)
repository is registered as a **disabled, licence/data-review-gated geospatial
reference**. It is visible in Jinwoo's Framework Registry and can produce a
bounded safety dry run. It does **not** add a globe, live data layer, tracker,
map tile, camera feed, voice feature, browser/device permission, API key,
proxy, socket or upstream runtime.

Jinwoo Native remains the canonical mission engine. It retains responsibility
for policy, explicit approval, privacy, workspace confinement and redacted local
audit records.

## Source review record

Public repository metadata, the root `LICENSE`, `README`, `DATA_SOURCES.md`,
`SECURITY.md`, package manifest and root-tree entries were reviewed on
**2026-09-03** at commit:

```text
65bc522f49dc1166eca533996be8e789ad36cfe5
```

No repository was cloned. No archive was unpacked for this batch. No upstream
source, dependency, asset, model, key, script, server or generated output was
copied, installed, linked, bundled, invoked or executed.

| Adapter ID | Project | Runtime described upstream | Source licence result | Jinwoo owner | Current state |
| --- | --- | --- | --- | --- | --- |
| `gods-eye-view` | God's Eye View — Geospatial Safety Intake | JavaScript/Vite/Cesium browser application | MIT applies to source code **only**; third-party live data, bundled datasets and 3D assets retain their individual terms | Tank | **Licence/data/asset review required; execution disabled** |

GitHub repository metadata did not provide an SPDX licence value at review time,
but the reviewed root `LICENSE` contains the MIT text. That same licence file
explicitly states that its grant does not extend to third-party data or assets.
Examples called out by the upstream file include provider terms, attribution,
non-commercial/share-alike datasets and separately licensed 3D models. The
source-code MIT grant is therefore not enough to adopt the bundled application
or its data layers as one package.

## Why it is not an active integration

The upstream project documents a photorealistic WebGL globe with real/public
spatial information such as aircraft, vessels, satellites, earthquakes, traffic,
radio, mapped locations and public-camera layers. It also contains a voice route
and browser-oriented provider/proxy architecture. Those capabilities carry
privacy, surveillance, data-licence, attribution, network, location and cost
considerations that are outside Jinwoo's current local-first V1 boundary.

Accordingly, Jinwoo does not:

- fetch, display, cache, relay or track live aircraft, vessels, satellites,
  traffic, radio, camera, location or other spatial feeds;
- start Cesium, Google Maps, OpenAI, OpenSky, AIS, map-tile, WebSocket or proxy
  routes;
- request microphone, camera, screen, browser-location or device permissions;
- create an OSINT, surveillance, individual-tracking, monitoring or alerting
  workflow;
- copy or bundle the upstream JavaScript, CSS, assets, 3D models, datasets,
  configuration, scripts or launchers; or
- accept or store any related credential, token, provider key or location data.

The controlled record preserves only safe, high-level concepts:

1. non-live geospatial visualisation design;
2. data provenance and attribution UX; and
3. privacy-aware public-source boundary planning.

## What is implemented locally

- `GET /api/frameworks` exposes the `gods-eye-view` Batch 08 contract.
- `POST /api/frameworks/gods-eye-view/dry-run` produces a local, policy-screened
  planning result with `external_runtime_invoked: false`.
- The record is `license-review-required`, `execution_enabled: false`, and
  appears in the dashboard's searchable Framework Registry—even while the API
  is offline through the frontend fallback registry.
- `POST /api/control/review` verifies that the Batch 08 record remains present,
  licence-gated and non-executing.
- Backend regression tests assert the record's state, a three-role maximum dry
  run, no external invocation, and the live-data/camera restrictions.
- `scripts/check_safe_intake.py` rejects the reviewed Cesium/geospatial runtime
  dependency set from Jinwoo's manifests until a future explicit activation
  review updates that guard.

## Required activation gate

No visualization, source code, asset, live-data feed or provider from this lane
can be enabled until all applicable requirements are complete:

1. Pin the exact source version and review its source-code licence/NOTICE.
2. Inventory every selected dataset, API, map imagery, model and media asset;
   resolve licence, attribution, commercial-use, retention and redistribution
   requirements individually.
3. Define a narrow, purpose-limited use case that prohibits individual tracking,
   surveillance, sensitive-location monitoring and automated alerts unless a
   separate lawful/privacy review explicitly authorises it.
4. Do not use public-camera feeds, live identity-linked data or private/location
   data without a dedicated privacy, legal, consent and retention review.
5. Keep all providers, maps, telemetry, voice, camera/microphone and browser
   permissions disabled by default. Each route needs a separate visible consent
   and approval boundary.
6. Implement strict egress/SSRF protections, data minimisation, rate/depth/size
   limits, provider-side key restrictions, attribution and auditable source
   provenance before any networked retrieval is considered.
7. Keep any eventual tool/action proposal under Jinwoo policy, explicit approval,
   selected-workspace confinement, redacted audit records, local/offline tests,
   timeout/stop controls and a disable path.

## Final boundary

Batch 08 is a **registry and planning safety intake only**. It does not turn
Jinwoo into a live intelligence, map, tracking, camera, voice, monitoring,
browser, location or surveillance application.
