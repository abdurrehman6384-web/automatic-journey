# Controlled Integration Batch 02

**Status:** adapter contracts and Tank's no-fetch planning gate are implemented. No Batch 02 upstream package, source file, service, browser, crawler, container, model provider, or coding runtime is installed or executed by Jinwoo.

**Scope approved by the owner:** AG2, OpenHands, Firecrawl, Firecrawl Web-Agent, and Crawl4AI, in that order. The entries below are controlled integration lanes, not a second autonomous command system. Jinwoo's visible mission engine remains canonical.

## Reviewed upstream references

| Adapter ID | Project | Upstream source | Observed HEAD | Licence | Jinwoo owner | Contract state |
| --- | --- | --- | --- | --- | --- | --- |
| `ag2` | AG2 | <https://github.com/ag2ai/ag2> | `026c6c526b1c846436994f3d0e6930ffea49572b` | Apache-2.0 | Bellion | Contract-ready, execution disabled |
| `openhands` | OpenHands | <https://github.com/OpenHands/OpenHands> | `50144692e3695c84000577cddf3e848f8c8d9647` | MIT | Igris | Contract-ready, execution disabled |
| `firecrawl` | Firecrawl | <https://github.com/firecrawl/firecrawl> | `162e660426f2f1fa2947eceecef1244bc7f35600` | AGPL-3.0 | Tank | **Licence review required; execution disabled** |
| `firecrawl-web-agent` | Firecrawl Web-Agent | <https://github.com/firecrawl/web-agent> | `f023adf1cd1f731e27fdc844af62996f6c2a41c4` | MIT | Tank | Contract-ready, execution disabled |
| `crawl4ai` | Crawl4AI | <https://github.com/unclecode/crawl4ai> | `862f6bccb9c063f49b9d42701baa0eea17a4993f` | Apache-2.0 | Tank | Contract-ready, execution disabled |

Observed commits are review pins, not dependency pins or a commitment to distribute any upstream code. No upstream source has been copied into this repository.

## What was implemented locally

- The framework registry exposes all five records through `GET /api/frameworks`, with runtime/category, licence, commander owner and readiness status.
- `POST /api/frameworks/{framework_id}/dry-run` now provides a bounded, policy-screened plan for every Batch 02 adapter. It accepts 1–450 logical agents but proposes no more than Planner, Executor and Verifier (three runtime workers); `external_runtime_invoked` is always `false`.
- Batch-specific guardrails are included in dry-run output:
  - **AG2:** Bellion remains the only routing authority; provider/tool/approval choices stay in Jinwoo.
  - **OpenHands:** requires a future isolated sandbox and selected Workspace Guard root; no shell command, patch, git action or install without visible approval.
  - **Firecrawl / Web-Agent / Crawl4AI:** dry runs make no request and may not use browsers, cookies, authenticated sites, private networks or workspace uploads.
- Tank's **Research Gate** is a Jinwoo-native no-fetch planner at `POST /api/research/plan` and in the dashboard. It validates up to 10 explicit public HTTPS domain URLs without opening them, resolving DNS, starting a browser or calling an upstream framework. It rejects literal IP addresses, localhost, local/internal hostnames, non-standard ports, URL credentials and credential-like query keys. Plans are audited with metadata only; topic text and URLs are not added to audit detail.

## Firecrawl licence boundary

Firecrawl is marked `license-review-required` because its reviewed repository is AGPL-3.0. The current local contract does **not** import, bundle, execute, link to, or distribute Firecrawl code. Before any Firecrawl runtime, container, hosted endpoint, or copied code is enabled, the project owner must make and document a distribution/deployment compatibility decision with appropriate legal review. A dry-run or no-fetch Tank plan does not satisfy that activation requirement.

## Activation checklist — individual adapter only

None of these checks is complete merely because a record appears in the registry. Each adapter needs its own approved change with all of the following:

1. Reconfirm the release tag/commit, dependency graph, source integrity and current licence. Recheck Firecrawl's AGPL obligations before any related runtime work.
2. Implement an adapter that accepts work **only** from Jinwoo's approved mission path; no background agent, autonomous chat loop or direct UI-to-framework route.
3. Keep credentials out of prompts, URLs, browser profiles, audit logs and the frontend bundle. Cloud/model routes require explicit per-mission permission.
4. For **OpenHands**, use a disposable sandbox with no host credentials, narrow mounts only under Igris's selected workspace root, no automatic patch/apply/git/network/install path, output caps, timeout and retained audit evidence.
5. For **web collection/research**, validate DNS and connection targets again at execution time to resist rebinding; allow only explicit user-approved public domains; deny local/private/link-local/multicast/reserved ranges; enforce robots/terms review, rate/concurrency/response-size/depth/domain caps, citation and local retention policy. Do not use logged-in browser contexts or cookies by default.
6. Add offline tests proving that a policy block, missing approval, out-of-workspace path, private URL, sensitive value, failed network guard, or licence gate prevents every upstream invocation.
7. Keep the initial runtime disabled until the owner reviews test evidence and expressly enables that exact pinned adapter. Do not install an upstream package simply to make its status appear detected.

## Deliberately out of scope for Batch 02

- No crawling, searching, browser automation, browser profile access, URL fetch, DNS lookup, upload, external model request, container launch, terminal command, code patch, git operation or package installation.
- No Firecrawl distribution or integration while the AGPL decision is unresolved.
- Batch 03 is registered as a controlled-contract lane. See [`INTEGRATION_BATCH_03.md`](INTEGRATION_BATCH_03.md); it still does not enable an upstream package, gateway or scanner runtime.
- Batch 04 adds controlled advanced-skill lanes. See [`INTEGRATION_BATCH_04.md`](INTEGRATION_BATCH_04.md); it does not enable a CLI, agent loop, container, browser, desktop controller, voice/vision route or mobile runtime.
