# Branching policy

- `develop` is the base branch for normal development work, including code, documentation, tests, and routine fixes.
- `main` is reserved for intentional promotion/release flow and exceptional hotfixes.
- Agents and automation must set the PR base explicitly; they must not rely on the repository default branch.
- After opening a PR, verify its base branch. A normal feature/docs PR targeting `main` must be retargeted to `develop` before merge.
- The `PR base guard` workflow rejects normal feature/docs branches that target `main`.
