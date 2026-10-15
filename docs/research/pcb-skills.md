# Claude Code skills and plugins for PCB design: shortlist and security review

Date: 2026-10-14. Scope: KiCad review, DFM/DRC, BOM and part selection (LCSC/JLC/Digi-Key), datasheet checking, fab ordering. Nothing was installed, enabled or run. Repos were shallow-cloned to a throwaway scratchpad and read only.

Legend: [V] read on the primary source (repo files, GitHub API) in this session. [I] inferred or taken from a listing or secondary page.

## Bottom line

- Nothing here is installable "as is" without caveats, but one candidate is good enough to trial: **kicad-happy** (rank 1).
- Anthropic's official sources have nothing for KiCad or PCB work. [V] `anthropics/skills` lists 17 general skills (docx, pdf, mcp-builder, and so on). The `claude-plugins-official` marketplace (315 entries, fetched from `main`) has no KiCad, PCB or EDA plugin; the only hardware-adjacent entry is `cwc-makers` (a Cardputer flasher). Locally installed: plugins `superpowers` and `mattpocock-skills`; no hardware skills in `~/.claude/skills`; no `.claude/` directory in the repo.
- This project already has what the CLI-wrapper skills offer: `hardware/carrier-jlc/scripts/export_fab.sh`, `check_silk.py`, and `fab/drc.rpt`, `erc.rpt`, BOM and CPL CSVs, gerbers, renders. [V] (directory listing only; I did not read these scripts.) A `kicad-cli` wrapper skill would add little.
- Recommendation: **install kicad-happy pinned to a tag, for review only (read-only analysis), and also write a small project-local skill** (`jlc-order-prep`, see the end) that encodes this project's own rules and the "verified vs inferred" convention. The local skill is the higher-value, lower-risk item; kicad-happy is the better "second pair of eyes".

## Ranked shortlist

### 1. aklofas/kicad-happy (Claude Code plugin, 11 skills)

| Field | Value |
|---|---|
| Maintainer | aklofas (account since 2009, 31 repos, 54 followers); effectively single-maintainer (788 of 811 contributions) [V] |
| Stars / forks / issues | 1,394 / 129 / 3 open [V, `gh`, 2026-10-14] |
| Created / last commit | 2026-03-09 (about 7 months old) / 2026-10-14 (commit 6a91aaa) [V] |
| Licence | MIT [V] |
| Latest release | v2.3.1, 2026-10-06 [V]. Also listed in VoltAgent/awesome-agent-skills [V] |

What it does for this project:
- `kicad`: parses `.kicad_sch`/`.kicad_pcb`/gerbers (KiCad 5 to 10) with its own pure-Python S-expression parser. Reports schematic bugs, net tracing, schematic-vs-PCB cross-check, DFM scoring, power tree and regulator checks, thermal estimates, impedance. Our board is KiCad 10 and already has a schematic and PCB. [V, SKILL.md]
- `jlcpcb`, `lcsc`, `bom`: JLC capability tables, basic vs extended parts, BOM/CPL column format, LCSC part lookup (stock, price, basic/extended). [V]
- `datasheets`: structured extraction from datasheet PDFs for the analyzers (pairs well with our "verified vs inferred" rule). [V]
- `emc`, `spice`: EMC pre-compliance heuristics, ngspice runs (needs a local simulator). `digikey`, `mouser`, `element14`, `pcbway`: optional distributor skills that need API keys. [V]

Security assessment (read of SKILL.md files, plugin.json, and every `.py`/`.sh` by grep plus targeted reads):
- Manifest: `plugin.json` / `.claude-plugin` marketplace entry only. No hooks, no `.mcp.json`, no `allowed-tools` frontmatter, no settings changes. [V]
- Dependencies: README states zero required third-party packages, and a grep of imports confirms stdlib plus optional `yaml`/`jsonschema`. No requirements file, no `pip install` step. [V]
- Code execution: no `eval`, `exec`, `shell=True`, `os.system`, `pickle`, `marshal`, or `base64` anywhere in `skills/`. [V] `subprocess` is used only with fixed argv lists for `pdftotext`, `pdfinfo`, `gh auth status`, `ngspice`/`ltspice`/`xyce`, and the project's own analyzer scripts. [V]
- Network (all over urllib/requests, opt-in by running the scripts):
  - `jlcsearch.tscircuit.com` (third-party community mirror of the JLC catalogue, not JLCPCB; it receives your MPN/LCSC queries). `wmsc.lcsc.com` and `datasheet.lcsc.com` for datasheet PDFs. [V]
  - `api.digikey.com`, `api.mouser.com`, `api.element14.com`: only when the matching env vars are set. [V]
  - Datasheet fetchers download PDFs from manufacturer sites named in API responses and run `pdftotext` on them (parser exposure to untrusted PDFs, and datasheet text is untrusted input to the model). [V]
  - Optional `playwright` fallback (`pip install playwright && playwright install chromium`) in the sync scripts, only if you install it. [V]
  - `lifecycle_audit.py` (called via `--lifecycle`) sends BOM MPNs to those services. [V]
  - `action/entrypoint.sh` (GitHub Action) posts a commit status with `GITHUB_TOKEN`; only relevant if you wire the Action into CI. We would not. [V]
- Credentials requested: `DIGIKEY_CLIENT_ID/SECRET`, `MOUSER_PART_API_KEY`, `MOUSER_SEARCH_API_KEY`, `ELEMENT14_*`; `LTSPICE_PATH`, `NGSPICE_PATH`, `XYCE_PATH`, `SPICE_SIMULATOR` are paths only. All optional; LCSC/JLC search needs no key. [V]
- Flags:
  1. `digikey`, `mouser`, `element14` SKILL.md tell the agent to run `export $(grep -v '^#' ~/.config/secrets.env | grep -v '^$' | xargs)` if a central secrets file exists. Do not create that file; if you ever add keys, put them in a scoped env, not a shared secrets file. [V]
  2. `bom/scripts/edit_properties.py` rewrites symbol properties in the `.kicad_sch`. Our schematic is generated by `gen_sch.py`, so edits would be silently overwritten (or worse, diverge). Use review-only. [V, I for the overwrite consequence]
  3. SKILL.md text strongly steers the agent ("SPICE is required", run N analyzers). That is behavioural, not malicious, but review its output with the same skepticism as any model output. [V]
  4. Plugin install is all-or-nothing (11 skills). Mitigation: simply do not set any API keys; the distributor skills then do nothing useful.
  5. Fast-moving single-maintainer repo (788 commits in 7 months): a later update could add anything. Pin to a tag and re-read the diff before bumping. [I]
- Quality caveat: findings are heuristic; it states confidence labels and evidence, but expect false positives and some misses. [I, not tested on our board.] Treat it as an additional reviewer, not a gate.

Install (for you to run later; pinned to the reviewed release, not the moving `main`):
```
/plugin marketplace add aklofas/kicad-happy#v2.3.1
/plugin install kicad-happy@kicad-happy
```
(The README documents the `#<tag>` form for release candidates; I did not confirm that it also accepts a stable tag, [I].) I reviewed commit 6a91aaa, which is exactly 1 commit ahead of the v2.3.1 tag (0640846) [V, GitHub compare API]; diff those two before installing so the pinned tag matches what was reviewed. Try it first on a copy of `hardware/carrier-jlc` with no API keys set and no network (or only LCSC lookups).

### 2. Averyy/pcbparts-mcp (remote MCP for part search)

| Field | Value |
|---|---|
| Maintainer | Averyy [V] |
| Stars / last commit / licence | 125 / 2026-10-14 / MIT [V] |

What it does: search JLCPCB (575K+ in-stock parts), Mouser, DigiKey in one MCP; parametric filters, "find alternatives", JLC stock check, pinouts from EasyEDA, KiCad footprints via SamacSys, 285 reference boards, 41 design-rule notes. No API key for JLC. [V, README]

Security assessment:
- The documented install points Claude at a **hosted third-party service**: `claude mcp add -s user --transport http pcbparts https://pcbparts.dev/mcp`. Every query (part numbers, specs, so effectively your BOM) goes to a server run by one person; no stated retention or privacy policy found [V: grep of README/docs/landing for privacy/telemetry found nothing]. Rate limit 100 req/min per IP.
- Tool results are third-party data entering the model context (prompt-injection channel). It can only return data, but a compromised or malicious server could try to steer the agent.
- Self-hosting is supported (`uv pip install -e .` or Docker; local server on `localhost:8080`). Dependencies are pinned in `pyproject.toml`, including `wafer-py` described as an "anti-detection HTTP client (TLS fingerprinting, WAF solving)", which means the maintainer's scrapers evade bot protection on JLCPCB and others [V]. This is a ToS and reliability risk for the data source, not a risk to your machine.
- Credentials: none required; optional `MOUSER_API_KEY`, `DIGIKEY_CLIENT_ID/SECRET` (only for self-hosting). [V]
- Use `-s project` or `-s local`, not `-s user`, if you try it, and do not pass `auto-approve` for its tools.

Worth it only if you want conversational "find an equivalent C-number" searches. kicad-happy's `lcsc` skill covers basic LCSC lookup without a standing network service.

Install: `claude mcp add -s local --transport http pcbparts https://pcbparts.dev/mcp` (hosted), or self-host as above.

### 3. American-Embedded/kistack (KiStack, 10 skills, "human written")

| Field | Value |
|---|---|
| Maintainer | American Embedded, LLC [V] |
| Stars / last commit / licence | 399 / 2026-09-24 / MIT with an extra clause (logo may not be reproduced); GitHub reports "other" [V] |

What it does: instruction-only skills (bom, export, footprint, gerbers, layout, panelize, pcb, pcb-product-render, schematic, symbol). The `kicad-bom` skill has sensible part-selection rules (capacitor DC-bias derating, dielectric, resistor power rating, never edit BOM output, JLCPCB BOM column preset). `kicad-export` wraps `kicad-cli` with 3,551 lines of CLI reference. [V]

Security assessment:
- Only one script (`export/scripts/convert_position.py`, a CSV column converter, stdlib only). No network code, no subprocess in scripts. [V]
- SKILL.md files tell the agent to use remote MCPs `https://pcbparts.dev/mcp` or `https://api.zenode.ai/mcp/` (same concerns as rank 2) and to `git clone` the official KiCad `kicad-library-tools` and `klc` repos from GitLab (footprint/symbol skills). `pcb-product-render` mentions a private LAN gallery URL (author's setup leaking into the skill, harmless). [V]
- Install route is `npx skills add American-Embedded/kistack`, which executes the npm `skills` CLI (code you have not reviewed). Safer: copy the `skills/<name>` directories you want into `~/.claude/skills/` manually after reading them. [V for the command, I for the npm package contents]
- Overlap: largely redundant with what `export_fab.sh` and the existing drc/erc reports do; the `bom` and `pcb` review prose is the only novel part, and it is small enough to fold into our own skill.

### 4. FradSer/dotclaude, `hardware` plugin (`use-kicad-cli`, `use-openscad`)

| Field | Value |
|---|---|
| Maintainer | FradSer (Frad LEE), 593 stars [V] |
| Repo created / last commit / licence | 2025-08-04 / 2026-10-09 / MIT [V] |

What it does: a careful `kicad-cli` operating guide (macOS binary path, exit-code gotcha for DRC/ERC, deprecated flags). Sound content. Written for KiCad 9.0; our boards are KiCad 10. [V]

Security: instruction-only plus a Dockerfile for OpenSCAD; no hooks or MCP; the marketplace is the maintainer's 20-plugin collection (git, office, lark, marketing, ...), so `marketplace add` registers all of them as installable even if you enable only `hardware`. [V] Value is low here because `export_fab.sh` already exists. Listed for completeness; skip unless you rewrite the export pipeline.

Install: `/plugin marketplace add FradSer/dotclaude` then `/plugin install hardware@frad-dotclaude`.

## Not recommended

| Candidate | Reason |
|---|---|
| mixelpixx/KiCAD-MCP-Server (2,692 stars, MIT, v2.8.2, active) [V] | Large Node + Python MCP server that drives KiCad's pcbnew API and mutates boards live; spawns Python subprocesses and `exec`s shell probes; `setup-macos.sh` runs `pip install -r requirements.txt` into KiCad's Python; calls jlcsearch, LCSC, DigiKey, JLCPCB APIs; optional `JLCPCB_APP_ID/API_KEY/SECRET`. Large attack surface. More importantly our PCB is generated from Python scripts, so interactive board edits would be lost on the next build. |
| oaslananka/kicad-mcp-pro (130, MIT, active) [V] | 96 `subprocess`/`os.system` hits in `src`, tray/dashboard/Docker/OpenTelemetry options (telemetry claimed off by default); a lot of surface for a project that does not need live editing. Not deeply audited. |
| lamaalrajih/kicad-mcp (527, MIT) [V] | Stale: last commit 2025-10-17, over a year old; targets KiCad 9. |
| Seeed-Studio/kicad-mcp-server (150) [V metadata only] | No licence file reported; MCP editing server; not audited. |
| hulryung/jlcpcb-skill-mcp (2 stars, **no licence**) [V] | 2 stars, 3 months old, no licence; ships an MCP built via `npm install` / `npx -y`. Too little track record. |
| BeckhamLabsLLC/kicad-jlcpcb (25, MIT) [V metadata + README] | Generates a `.kicad_pcb` for EasyEDA auto-routing: opposite of our workflow (generated PCB, JLC order). `npx -y` MCP plus EasyEDA account/lookups. |
| Eyalm321/jlcpcb-mcp (2), mageoch/JLCPCB-MCP (0), xX-alex1337-Xx/jlcpcb-mcp (0), yigitabi5444/JLCPCB-MCP (0) [V metadata] | Near-zero adoption; not audited. |
| telagod/code-abyss (`operating-kicad-eda`, 244) [I] | General multi-skill dump; the KiCad skill is aimed at autoroute-and-export pipelines (FreeRouting), not review. Not opened. |
| Zane456/PCB-Agent-Teams (75, non-standard licence), l3wi/claude-eda (19, no licence), mattpainter701/kicad_automations (20), major-ai-skills `kicad` [V metadata / I] | Opinionated multi-agent workflows to draw boards; low adoption; some without licences. Not audited. |
| Digi-Key / Mouser / Octopart (Nexar) official MCPs | None found in the official marketplace. [V for the marketplace; I for the wider web.] DigiKey/Mouser need personal API keys anyway. |
| Community awesome lists (hesreallyhim/awesome-claude-code, travisvn, ComposioHQ) | grep for kicad/pcb/schematic/electronics found nothing hardware-relevant; only VoltAgent/awesome-agent-skills lists kicad-happy. [V] |

## Is a project-local skill better? Yes, as the primary tool

The review-quality gains from any third-party skill are modest compared to encoding what is specific to this board and this fab. A small repo skill, e.g. `.claude/skills/jlc-order-prep/SKILL.md` (about 60 lines, no scripts, no network), would:

1. Run the existing pipeline (`scripts/build.sh`, `scripts/export_fab.sh`) and require `drc.rpt` and `erc.rpt` to show zero violations or only listed, justified exclusions.
2. Check the BOM CSV: every row has an LCSC `C` number; flag extended parts (per-part fee); confirm stock/price from a fresh lookup and record the date; column headers exactly `Comment, Designator, Footprint, LCSC Part #`.
3. Check the CPL: designators match the BOM; rotation offsets for known-problem footprints are verified against the JLC 3D preview (a manual step the user must do).
4. Check silkscreen with `check_silk.py`, board outline, and the fab spec the order page needs (layers, thickness, finish, min trace/space, via drill) against the JLC capability table.
5. Enforce the repo rules: nothing from `captures/`, serial-number registers scrubbed, no secrets in files, and keep **verified vs inferred** separate in the order notes; no static values (the JLC capability numbers go in a config file, not the skill body).
6. Output a go/no-go checklist the user signs off before uploading; it never uploads or orders anything itself.

This costs nothing in trust, is TDD-friendly (the checks can be a pytest over the `fab/` outputs, per the repo's TDD rule), and can borrow the useful prose from kicad-happy's `jlcpcb` skill and KiStack's `kicad-bom` rules after you have read them.

## Method and limits

- Read: kicad-happy (SKILL.md for kicad, jlcpcb, lcsc, bom, datasheets in part; plugin.json; grep audit of all scripts for network, subprocess, eval-class calls, env vars, URLs), pcbparts-mcp (README, pyproject, source URL grep), kistack (SKILL.md for bom/pcb/export in part; script), FradSer hardware plugin (manifest, use-kicad-cli SKILL.md), mixelpixx (package.json, exec/spawn sites, setup script grep), oaslananka (README/grep only). All at the commits cloned on 2026-10-14.
- Not done: no code was run; not every file of any repo was read; transitive npm/PyPI dependencies were not audited; "not recommended" entries marked [V metadata] were judged from GitHub metadata and README only.
- Commit counts and "single maintainer" come from the contributors API for kicad-happy only.
