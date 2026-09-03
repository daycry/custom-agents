# cybersecurity — Phase 1 GATHER in full: reconnaissance, scope modes and special handling

> Reference for the `cybersecurity` skill. Read it **only** when you start Phase 1 (GATHER) — before spawning any agent — and when you need the exact rules of `--scope` / `--focus` or the special cases (monorepo, test code, generated code, vendored code). The condensed flow lives in `SKILL.md`.

## Phase 1: GATHER — Reconnaissance

Before spawning any agents, YOU (the orchestrator) must gather context. This phase is
CRITICAL — agents without context produce noise.

### Step 1.1: Detect Project Type and Tech Stack

Run these commands to understand the project:

```bash
# Languages present
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" -o -name "*.java" -o -name "*.go" -o -name "*.rs" -o -name "*.rb" -o -name "*.php" -o -name "*.cs" -o -name "*.swift" -o -name "*.kt" -o -name "*.c" -o -name "*.cpp" -o -name "*.h" -o -name "*.sh" -o -name "*.bash" \) | head -200

# Package managers / dependencies
ls -la package.json package-lock.json yarn.lock pnpm-lock.yaml Pipfile Pipfile.lock requirements.txt pyproject.toml Cargo.toml go.mod go.sum Gemfile Gemfile.lock composer.json pom.xml build.gradle 2>/dev/null

# IaC files
find . -type f \( -name "*.tf" -o -name "*.tfvars" -o -name "Dockerfile" -o -name "docker-compose*.yml" -o -name "*.yaml" -o -name "*.yml" \) -not -path "*/node_modules/*" -not -path "*/.git/*" | head -50

# CI/CD
ls -la .github/workflows/ .gitlab-ci.yml Jenkinsfile .circleci/ .travis.yml bitbucket-pipelines.yml 2>/dev/null

# Framework indicators
grep -rl "from django" --include="*.py" -l 2>/dev/null | head -3
grep -rl "from flask" --include="*.py" -l 2>/dev/null | head -3
grep -rl "from fastapi" --include="*.py" -l 2>/dev/null | head -3
grep -rl "express\|next\|nuxt\|react\|vue\|angular\|svelte" --include="*.json" -l 2>/dev/null | head -3
grep -rl "spring\|quarkus\|micronaut" --include="*.java" --include="*.xml" --include="*.gradle" -l 2>/dev/null | head -3
```

Record findings as:
- **Project type**: web app | API | CLI | library | IaC | mobile | monorepo | microservices
- **Languages**: [list with % estimate]
- **Frameworks**: [list with versions if detectable]
- **Package managers**: [list]
- **IaC present**: yes/no [which tools]
- **CI/CD present**: yes/no [which platform]

### Step 1.2: Scope Determination

Based on the `--scope` argument (default: `full`):

| Scope | What to analyze | When to use |
|-------|----------------|-------------|
| `full` | Entire repository | First audit, comprehensive review |
| `quick` | Entry points + auth + secrets + deps only | Fast check, CI integration |
| `diff` | Only changed files (git diff) | PR review, incremental audit |

For `diff` scope:
```bash
git diff --name-only HEAD~1..HEAD 2>/dev/null || git diff --name-only --cached 2>/dev/null || git diff --name-only
```

For `full` scope, enumerate ALL source files (excluding node_modules, vendor, .git, build artifacts).

### Step 1.3: Entry Point Enumeration

Identify all places where untrusted data enters the application:

- **HTTP routes/endpoints** — grep for route decorators, router definitions, handler registrations
- **API endpoints** — REST, GraphQL resolvers, gRPC service definitions
- **CLI argument parsing** — argparse, commander, cobra, clap
- **File uploads** — multipart handlers, file processing
- **WebSocket handlers** — real-time data ingestion
- **Queue consumers** — message processing from external queues
- **Scheduled tasks / cron** — jobs that process external data
- **Environment variables** — especially those used in security-critical paths

### Step 1.4: Trust Boundary Mapping

Identify where data crosses trust levels:

```
[Untrusted] User input → [Processing] Application logic → [Trusted] Database/Storage
[Untrusted] External API → [Processing] Data transformation → [Trusted] Internal state
[Untrusted] File upload → [Processing] File parsing → [Trusted] File storage
[Untrusted] Environment → [Processing] Configuration → [Trusted] Runtime behavior
```

For each boundary, note: What crosses? How is it validated? What could go wrong?

### Step 1.4b: STRIDE Threat Analysis Per Boundary

For EACH trust boundary identified above, systematically evaluate all 6 STRIDE categories:

| STRIDE Category | Question to Ask | Routed to Agent |
|----------------|-----------------|-----------------|
| **Spoofing** | Can an attacker impersonate a legitimate user/service at this boundary? | Agent 2 (auth) |
| **Tampering** | Can data be modified in transit or at rest across this boundary? | Agent 1 (vuln) + Agent 8 (logic) |
| **Repudiation** | Can an actor deny performing an action? Is there audit logging? | Agent 1 (logging/A09) |
| **Information Disclosure** | Can sensitive data leak across this boundary? | Agent 3 (secrets) + Agent 1 |
| **Denial of Service** | Can this boundary be overwhelmed or made unavailable? | Agent 5 (IaC) + Agent 8 (rate limits) |
| **Elevation of Privilege** | Can a lower-privilege actor gain higher access here? | Agent 2 (auth) + Agent 8 (logic) |

Include STRIDE findings in the PROJECT CONTEXT payload so agents know which threats apply to their scope.

### Step 1.5: Build Context Payload

Compile all gathered information into a structured payload that EVERY agent receives:

```
PROJECT CONTEXT:
- Type: [web app / API / CLI / library / IaC / mobile]
- Languages: [list]
- Frameworks: [list with versions]
- Package managers: [list]
- Entry points: [list with file:line locations]
- Trust boundaries: [list]
- Scope: [full / quick / diff]
- IaC: [terraform / docker / k8s / github-actions / none]
- CI/CD: [github-actions / gitlab / jenkins / none]
- File count: [N source files]
- Compliance target: [pci / hipaa / soc2 / gdpr / none]
```

## Scope Modes

### `--scope full` (default)
All 8 agents, full codebase, complete report.

### `--scope quick`
Agents 1-4 only (vuln, auth, secrets, deps). Reduced context gathering.
Output: shortened report with Critical/High findings only.

### `--scope diff`
All 8 agents but ONLY on changed files (git diff).
Include surrounding context (functions/classes containing changes).
Output: diff-focused report showing findings in changed code.

### `--focus [agent]`
Single-agent deep dive: `vuln`, `auth`, `secrets`, `deps`, `iac`, `threat`, `ai`, `logic`.
That agent runs at maximum depth with full context. All others skipped.

## Special Handling

### Monorepo Detection
If multiple package.json / go.mod / Cargo.toml at different directory levels:
- Report findings per-service/per-package
- Look for cross-service vulnerabilities (shared auth, internal APIs without auth)

### Test Code
- REDUCE severity for findings in test files by one level (HIGH → MEDIUM)
- EXCEPT: hardcoded real credentials in test files remain HIGH
- EXCEPT: test files that are deployed to production (check build config)

### Generated Code
- Flag generated code (protobuf output, OpenAPI clients, etc.) separately
- Don't report style issues in generated code
- DO report security issues even in generated code

### First-Party vs Third-Party
- Findings in first-party code: full severity
- Findings in vendored/copied third-party code: note as "vendored dependency issue"
- Recommend updating the vendored code rather than patching inline
