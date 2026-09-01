# Controlled multi-agent framework adapters

Jinwoo's **native mission engine is canonical**. It owns mission routing,
Planner → Executor → Verifier roles, policy classification, approval gates,
workspace boundaries, and the future audit record.

Swarms, Agency-Swarm, and Ruflo are intentionally represented as optional
adapters rather than independent always-on orchestrators. This avoids three
competing control loops and preserves the local-first safety model.

## V1 behaviour

`GET /api/frameworks` is a read-only registry endpoint. It reports:

- **Jinwoo Native Engine** as the active canonical engine;
- **Swarms** only if its Python module is already installed locally;
- **Agency-Swarm** only if its Python module is already installed locally;
- **Ruflo** only if its local CLI is already available on `PATH`.

Detection is not activation. All three optional adapters have
`execution_enabled: false` in V1. The application does not install, invoke,
or send a mission to them automatically.

## Required activation gate for a later phase

An adapter can be made executable only after all of the following are reviewed
and implemented:

1. Pin a compatible version and review its licence and provider requirements.
2. Implement one narrow adapter contract with typed input/output.
3. Route every proposed action back through Jinwoo policy and user approval.
4. Restrict every file/tool operation to the user-selected workspace.
5. Record hand-offs, inputs, outputs, errors, and approval decisions in the
   local audit trail.
6. Add offline/no-key tests and a rollback path.

### Intended responsibility boundaries

| Integration | Intended later use | Boundary that remains with Jinwoo |
|---|---|---|
| Swarms | Selected hierarchical worker/specialist patterns | Mission lifecycle, policy, approval, audit |
| Agency-Swarm | Compatible role/organisation hand-offs | Mission lifecycle, policy, approval, audit |
| Ruflo | Optional local TypeScript/MCP developer-harness bridge | Mission lifecycle, policy, approval, audit |

This status-first boundary is deliberate: package presence must never silently
change the product's autonomy or privacy posture.
