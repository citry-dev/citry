# AGENTS.md - Citry example projects

These rules apply to every complete project under `examples/`.

- Read the repository-root `CLAUDE.md` and
  `docs/design/example_projects.md` before changing a project.
- Keep each starter independently copyable. It must not import another
  example, `examples/tests`, or repository-only helpers.
- Use public `citry` APIs and explicit component schemas.
- Keep host routing, lifecycle, security, and server setup visible and
  idiomatic for that host.
- Every web starter includes the shared Events and Alpine journey. The
  standalone starter deliberately has no Events transport.
- Keep data deterministic and make the default run independent of external
  services, CDNs, and network APIs.
- Run the project-local tests and the applicable shared qualification profile
  after a change.
- Update `examples/catalog.toml`, the project README, dependency lock, and
  discovery links when their claims change.
