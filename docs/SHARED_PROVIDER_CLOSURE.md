# Shared provider closure batch

## 1. Validated images

The before graph is preserved in `build/shared-provider-before/graph.json`.
The after graph is `build/shared-provider-report/graph.json`. Both use ordinary
CMake artifacts plus a fresh inventory of the same 805 original overlay C/C++
units. Neither inventory includes ad hoc SDK probes or temporary test objects.

Validated dylibs: **91 → 92**. Exact original-member linked images: **90 → 91**;
the separately counted existing protection replacement remains one. Binding
failures remain zero. OVY_18 is newly linked, with 288 validated import slots.
All previously validated images remain validated. Original image membership,
identities, pins and the upstream HeartGold checkout are unchanged.

## 2. Missing original members

Members without direct native object provenance: **435 → 385**, out of the same
1,751 distinct original members. This is provenance, not a count of missing game
implementations. The 50 newly represented members are 34 CPS/SSL objects, 15 Wi-Fi
objects and the Pokédex data object. No previously represented member disappeared.

Blocked original assembly conversions: **88 → 86**. The Pokédex and DWC lobby
state data members now have complete reviewed recipes. The lobby data member is
not emitted into a partial OVY_45 interface: its image remains excluded because
the chat data/consumer contract is still blocked. Temporary object tests validate
that new member independently, without counting it as whole-image provenance.

The NitroWiFi MD5 forwarding member remains in its existing runtime target;
it is not duplicated into the main archive. CPS/Wi-Fi selection follows original
`main.lsf` placement through the existing eligibility policy.

## 3. Actual failed image links

Selected overlay representations: **104 → 105**. Actual failed selected image
links: **13 → 13**. Fresh individual linker logs are in
`build/native-graph/link-failures/`; their initial versions are preserved under
`build/shared-provider-before/link-failures/`.

| Image | Before undefined symbols | After undefined symbols |
| --- | ---: | ---: |
| OVY_12 | 7 | 2 |
| OVY_39 | 21 | 21 |
| OVY_44 | 20 | 20 |
| OVY_46 | 9 | 9 |
| OVY_47 | 19 | 19 |
| OVY_48 | 8 | 8 |
| OVY_49 | 153 | 149 |
| OVY_73 | 28 | 28 |
| OVY_75 | 25 | 25 |
| OVY_80 | 1 | 1 |
| OVY_88 | 20 | 20 |
| OVY_90 | 3 | 3 |
| OVY_93 | 2 | 2 |

These sets overlap. OVY_12's remaining imports are DWC_GetLinkLevel (compiled in
incomplete OVY_0) and WM_GetLinkLevel (an original SDK provider not incorporated
by the current fork/build). The five genuine Pokédex popup providers are now
available through the complete OVY_18 representation.

All 153 original OVY_49 imports have been classified: **149 are genuine compiled
OVY_45 providers**, and four are explicit ARM compiler helpers in the instrument
source. All 149 remaining imports still require OVY_45; none is ignored.

The default build was attempted and still fails on the required dylibs. The game
executable link cannot yet be reached through the build. Its undefined-symbol
inventory remains unknown; observed object imports are not substituted for it.

## 4. Shared providers incorporated

The original CPS/SSL and Wi-Fi implementation families were probed with the
existing native compiler flags: 51/53 initially compiled; two contained ARM
inline functions. All 53 now compile in their original main-image ownership,
including three already selected SOC sources and the already represented runtime
MD5 member. This adds 49 original C members to direct provenance.

The CPS and WCM inline representations are guarded by hashes of the original
source and exact assembly fragments:

- Three CPS big-number digit-load functions preserve the original little-endian
  ARM r1:r0 return words and the original halfword accesses.
- WCM population count and leading-zero operations use native compiler operations;
  the original CLZ(0) result of 32 is explicit.
- Two CPS halfword products use unsigned intermediates, preserving the original
  low 32-bit ARM result. Sanitizers caught their signed-promotion overflow before
  this correction.

The OVY_49 compiler operations are source-guarded and bounded. Its soft-float
expressions add 0.5 to positive, exactly representable integer constants before
truncation. Native float locals preserve those intermediate values; no bit-pattern
value escapes those local calculations. Its long-multiply operands come from
signed 32-bit values, whose product fits signed 64 bits. Shift intermediates use
explicit 32-bit ARM wrapping. No global substitute helper provider was added.

The Pokédex conversion validates original `.size symbol,.-symbol` annotations as
storage-free metadata and retains its scalar template bytes and 17 callback
relocations. DWC lobby data preserves scalar channel-mode records and cookie
buffers, widens only proven pointer arrays/globals, and uses the actual native
two-pointer reserve-state size. It does not approve the separate chat member.

The twelve original CA records have independent source-byte, relocation and
consumer-layout tests. CpsRootCa occupies 40 native bytes: name at 0, scalar
modulus length at 8, modulus pointer at 16, scalar exponent length at 24 and
exponent pointer at 32. Their original scalar values are retained. This is not
approval of the complete `dwc_lib_data` member, whose other state is incompatible.

## 5. Remaining blockers by root cause

`cmake/native_obstructions.py` combines actual failed-image imports, incomplete
image imports, original member representations and source definition candidates.
Its output is `build/shared-provider-report/obstructions.json`, with every
observed obstruction and candidate owner. Candidate source definitions are
explicitly distinct from compiled exports; declarations do not authorize providers.
The ranking counts distinct affected failed/incomplete images, not references.

OVY_0 still affects 17 images, and OVY_45 affects eight. The incomplete main image
also obstructs 14 of the currently failed/incomplete images. These are direct
observed edges, not promises of immediate closure.

**OVY_0 data and consumer ABI:** all four data members remain blocked. Match-key
records are 12 bytes on ARM32 and 24 natively; the original consumer clears 1,848
bytes and performs 12-byte/raw-interior-label indexing. Native storage would need
3,696 bytes and consistent consumer offsets. The socket-error callback writes
`((int *)&gDwcControl)[1]`: natively this changes pointer bits rather than the
following original error slot. The GameSpy hostent/persist globals also span
public interior labels and pointer-bearing native structures; literal `-8` alias
construction is not a general native offsetof operation.

A newly isolated blocker is `static_qr2_rec`: `query_report_init.c` declares a
272-byte QueryReport with `u32` callbacks and userData. `server_report.c` declares
a 320-byte native QRRecord with typed callback and parameter pointers. Their
heartbeat offsets are 172 and 208. The original initializer also accepts callback
arguments as u32. A larger data allocation cannot repair either the call ABI or
the stores. Preserving those integer-held addresses needs a consistent reviewed
runtime representation or guest-ABI lowering; no unsafe rewrite is supplied.
CA typing alone therefore cannot complete this member or OVY_0.

**OVY_45 dispatch and consumer ABI:** the global/state member is represented, but
the separate chat member remains blocked. Original member-pointer Holders occupy
12 bytes with their method at 4; the actual native C++ type occupies 24 bytes with
its 16-byte PMF at 8. Manual LobbyRequest vtables have four native call pointers
at 0/8/16/24, not four-byte slots. Additionally, the original private MapNode view
in `lobby_chat_remove_channel.cpp` places the user-count field at 28; the native
canonical LobbyChannelMapNode places it at 48. Widening symbolic words cannot
repair this consumer view. The blocked metadata hashes the original consumers,
and reproducible probes retain these disagreements as unsupported conditions.
No partial OVY_45 or OVY_0 interface is emitted.

**Other original providers:** missing SDK objects (including WM), original ARM
runtime implementations and unrepresented original data still obstruct main and
other images. CPS/Wi-Fi C incorporation does not approve their main-owned state,
thread/context implementation or the complete networking subsystem. The
obstruction JSON lists the original source candidates and member reasons rather
than turning them into assumed exports. Ten original empty overlays remain empty;
the 18 missing encoded/encrypted protection members remain separate from the
existing authorized replacement. NitroMain has not executed.

## 6. Tests and regressions

- Fresh original overlay audit: **805/805**.
- Fresh ARM64 object inventory: **805/805**.
- All 92 actual dylibs pass the existing binding validator; no previous image is
  lost and no invalid bindings are introduced.
- Full CTest: **43/47 pass**, including the new shared-provider entry. The same
  four pre-existing failures remain: `real_metal_raster`,
  `global_terminal_native_images`, `native_g3_original_model`,
  `native_g3_commands_metal`.
- Focused CTest: **7/7** pass. Native source suite: **17** pass. Assembly suite:
  **18** pass. Data IR: **8** pass. Image graph: **4** pass. Obstruction unit: **1**
  passes.
- Shared-provider suite: **8** pass under the existing native toolchain. It runs
  the actual original CPS division provider against 10,000 quotient/remainder
  reference cases under ASan/UBSan, checks ARM helper boundary values, bounded
  instrument arithmetic, source drift, generated data/relocations, native state
  types, all twelve CA records and the unsupported DWC/Plaza ABI operations.

Rebuild the inventories without adding probe-only objects to the graph:

```sh
python3 -B tests/audit_overlays.py --build build --output build/shared-provider-audit --adapt
python3 -B tests/compile_native_objects.py --build build --audit build/shared-provider-audit/results.json --output build/shared-provider-objects
python3 -B cmake/native_graph_report.py --game upstream/pokeheartgold --build build --objects build/shared-provider-objects --diagnostic build/shared-provider-default-build.log --out build/shared-provider-report
python3 -B cmake/native_obstructions.py --graph build/shared-provider-report/graph.json --game upstream/pokeheartgold --out build/shared-provider-report/obstructions.json
```

The subsequent invariant checks, bounded member-pointer encoding and executable
ABI counterexamples are documented in [SHARED_ABI_BARRIER.md](SHARED_ABI_BARRIER.md).
