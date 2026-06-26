---
name: skill-creator
description: Use when creating a new Agent Skill or editing an existing one for this repo — authoring the SKILL.md, choosing a good name/description, structuring supporting files, and keeping skills focused and discoverable. Apply whenever the user asks to "make a skill", "add a skill", or improve one under .claude/skills/.
license: Adapted from anthropics/skills (https://github.com/anthropics/skills). See repo for full terms.
---

# Skill Creator

> Vendored/adapted from anthropics/skills. Use it to author or refine skills under
> `.claude/skills/` in this project.

## What a skill is
A folder containing a `SKILL.md` with YAML frontmatter plus instructions, and optionally supporting
files (scripts, references) the agent loads on demand. Skills teach repeatable, specialized workflows.

## Frontmatter (required)
```yaml
---
name: kebab-case-name        # matches the folder name
description: One or two sentences. State WHAT it does and WHEN to use it, with trigger phrases the
             user is likely to say. This is the only text always loaded, so make it precise.
---
```

## Authoring process
1. **Capture intent.** What concrete task should this make repeatable? Who/what triggers it?
2. **Write the description for discovery.** Lead with the trigger conditions ("Use when…"). Bad: a
   topic label. Good: actionable conditions + keywords the user would type.
3. **Keep the body focused.** Steps, conventions, and gotchas — not an essay. Prefer checklists and
   short code patterns. Link out to reference files for anything long.
4. **Make it project-aware.** Reference real files/commands in this repo so the skill is immediately
   usable (e.g. point at `Backend/app/services/...` or `socratic-frontend/...`).
5. **Test it.** Trigger the skill on a realistic request; confirm the description actually surfaces it
   and the steps lead to the right outcome. Tighten the description if it under/over-triggers.

## Structure conventions
```
.claude/skills/<name>/
  SKILL.md            # required
  reference/...       # optional: long docs loaded on demand
  scripts/...         # optional: helper scripts (document with --help, treat as black boxes)
```

## Quality checklist
- [ ] `name` matches the folder, kebab-case.
- [ ] `description` says what + when, with trigger words.
- [ ] Body is concise and actionable; long material is in `reference/`.
- [ ] References real repo paths/commands where relevant.
- [ ] Doesn't duplicate another skill's scope.
