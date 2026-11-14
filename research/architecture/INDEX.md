# Architecture memory

Resume from [architecture.json](architecture.json), the sole coverage/findings ledger.
Mission: [CODEX_PLAN.md](CODEX_PLAN.md). Baseline commit: `d4213f19` plus preserved
working-tree changes. Bounded passes are ongoing; this is not complete compiler review.

```text
build.sh -> profile_build.py -> CMake -> Make/Ninja
                                |
      pinned libntr manifests + original FX generator -> native SDK/host services
      original main.lsf -> native_image_graph -> generated CMake/image inventory
        -> native_sources (+ coordinated rules) -> native C/C++/headers -> archives
        -> original resource recipes/tools -> DS-layout data -> NARC/NAIX + assets
        -> optional guest32: ARM32 IR -> LLVM23 lowerer -> ARM64 objects/providers
      overlay selection + archives -> global emitted-provider contracts
        -> per-image interfaces/response files/fingerprints -> dylibs
        -> actual Mach-O binding checks -> heartgold -> dynamic-closure audit
      filesystem.mk + resources -> separate source cartridge image
      runtime: dyld binding/registration -> cartridge/PXI/NVRAM -> original NitroMain
        -> FS activates original overlay initializers; host owns native services
```

Five proven issues (certificates in JSON):

1. **AR-0001/0002, removed:** duplicate asset tool discovery and repeated object
   inspection; original conversion and rejection gates remain.
2. **AR-0006/0007, removed:** duplicate liveness analysis and manifest grammar.
3. **AR-0008/0010, removed:** repeated storage parsing and native-call marshaling;
   layout, admission and ABI checks retain distinct responsibilities.
4. **AR-0011/0012/0014, removed:** dead intermediate MB layouts, repeated task
   prototypes and 226 lines of redundant replacement context.
5. **AR-0004/0009, open:** missing native-registry/semantic-slot producers and
   historical admission witnesses prevent a proven cold guest closure.

Five unresolved questions:

- What minimal existing provider contract does guest32 state proof actually require?
- Which individual native adaptations are essential, redundant, or obsolete?
- Are all imported Python inputs/side effects declared in CMake, including recovery?
- Do source-built wireless providers reproduce the historical image/runtime boundary?
- Which guest/native layout, callback, and lifetime authorities can safely converge?

Verification: **151 units read/verified, 82 indexed**, including contract sections.
Of 423 baseline adaptation edits, **132 reviewed, 4 removed, 291 unreviewed**;
424 remain (four removed, five necessary ABI edits added). Last full `build/` baseline: configure passes, full build fails,
CTest **61/76 pass**. Last deletion pass: **4/4 focused CTests**; 815 adaptation
outputs audited. Removing intermediate edits preserves every output; sharing
prototypes changes only declaration lines in ten sources. All **21 MB fixture
compilations** preserve LLVM IR and diagnostics. Production reduction: **71 lines**.
These fixtures do not prove production MB overlay admission or task scheduling.
Earlier compiler/asset comparisons and validated overlay incrementality remain in
JSON. No cold-build or game-runtime equivalence claim. Prior work and clean pins
preserved. Evidence: [initial](evidence/first-pass.json),
[catalogs](evidence/guest32-catalogs.json), [state/ABI](evidence/state-and-bridge.json),
[multiboot](evidence/multiboot-contracts.json).

**AR-0014 removed:** duplicated unchanged context in 19 MB replacement rules:
**226 production lines / 17,934 bytes deleted**, no new mechanism or rule.
Whole-input hash checks and unique fragments remain. **815/815 adaptation records
identical**, **21/21 MB IR outputs/diagnostics identical**, **4/4 focused CTests**.
Every guard in the four reviewed records also rejects independent mutation.
[Evidence](evidence/mb-context.json). Earlier [beacon ABI repair](evidence/beacon-repair.json)
remains verified. **AR-0015 open:** pre-existing MB self-image bypass is unproven;
output equality does not establish its correctness.

Next exact action: `cat upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_parent_data.c`.
Then read `mb_parent_send_data.c` and both complete adaptation records. Trace reload
archive ownership/state completion before considering cache-view consolidation.
291 baseline edits remain unreviewed. Historical guest-input provenance and
provider/semantic-slot contracts remain unresolved.
