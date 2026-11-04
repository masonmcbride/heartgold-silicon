# Ten independent overlay identities

All ten identities are verified empty **of original members**, rather than missing
native implementations. No C, C++ or assembly object belongs to these images.
No archive, guest32 translation, dynamic library or entry point is added.

## Original evidence and lifecycle

`upstream/pokeheartgold/main.lsf` is the original linker membership specification.
Its ten blocks contain only `After`; the parser rejects unsupported overlay
object section selections and unknown directives (including libraries). The
native object/archive inventory therefore has no member or export to recover.
`After` specifies placement, not a symbol dependency or a load operation.

`global.inc` declares each identity exactly once. The SDK's
`lib/include/nitro/fs/overlay.h` maps `FS_OVERLAY_ID` to the original linker ID
symbol. The original SDK linker template,
`upstream/libntr/specfiles/ARM9-TS.lcf.template`, iterates every overlay, emits its
ID and file ID, filename, size, BSS size and static-initializer interval into
the overlay definitions/table. In the overlay section it emits one `WRITEW 0`
static-initializer terminator and aligns the section to 32 bytes even when the
object/library lists are empty. BSS has no members. Both
`heartgold.us/main.sha1` and `soulsilver.us/main.sha1` record
`de8a847bff8c343d69b853a215e6ee775ef2ef96` for every one of these files: the SHA-1
of exactly 32 zero bytes. These are padding-only original files, not zero-length
files. The classification checks both checksum manifests, declarations, numeric
IDs and placement, as well as the absence of object directives.

`rom.rsf` supplies the original overlay definitions and table to makerom.
`lib/NitroSDK/src/fs/FS_overlay.c` resolves table entries by numeric ID and opens
their ROM file ID; loading such an identity in the original ROM therefore needs
its actual 32-byte file. `FS_StartOverlay` skips the null initializer; ordinary
load/unload operations still apply. These IDs exist because the original linker
specification retains these positions in the 129-entry overlay inventory. The
source does not establish a further historical reason for reserving them.

A source/assembly search finds their names only in the LSF and `global.inc`
declarations (apart from the checksum manifests). There is no named game load
request or callback/export to port. This does not prove a computed numeric ID can
never reach the loader. The native representation retains the verified identity
and original file/table semantics in graph metadata, outside the executable
registry. No native dynamically loaded image is required by an identified game
call site. Arbitrary requests to load these IDs have **not** been runtime validated;
this change does not teach native FS to return success for them or bypass original
load/start/end/unload operations. ROM packaging would still need the original
files and table entries; no ROM packaging pipeline is changed here.

## Results

Evidence key **E**: original memberless LSF block + unique `global.inc` declaration
+ both variants' 32-zero-byte checksum + SDK linker section/table rules above.
All rows retain the listed original numeric overlay/file ID. “Metadata” means
verified graph identity with no native archive or dylib. No row is counted as a
linked executable image.

| Identity | Original member count | Original member filenames | Original overlay-table role | Native representation | Verification evidence | Final link status | Remaining blockers |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| OVY_9 | 0 | None | ID/file 9; After OVY_6; 32-byte padding image | Metadata | E | Verified empty; linking inapplicable | None for classification; runtime loading unvalidated |
| OVY_11 | 0 | None | ID/file 11; After main; 32-byte padding image | Metadata | E | Verified empty; linking inapplicable | None for classification; runtime loading unvalidated |
| OVY_66 | 0 | None | ID/file 66; After main; 32-byte padding image | Metadata | E | Verified empty; linking inapplicable | None for classification; runtime loading unvalidated |
| OVY_77 | 0 | None | ID/file 77; After main; 32-byte padding image | Metadata | E | Verified empty; linking inapplicable | None for classification; runtime loading unvalidated |
| OVY_79 | 0 | None | ID/file 79; After OVY_42; 32-byte padding image | Metadata | E | Verified empty; linking inapplicable | None for classification; runtime loading unvalidated |
| OVY_107 | 0 | None | ID/file 107; After main; 32-byte padding image | Metadata | E | Verified empty; linking inapplicable | None for classification; runtime loading unvalidated |
| OVY_125 | 0 | None | ID/file 125; After ds_protect; 32-byte padding image | Metadata | E | Verified empty; linking inapplicable | None for classification; runtime loading unvalidated |
| OVY_126 | 0 | None | ID/file 126; After ds_protect; 32-byte padding image | Metadata | E | Verified empty; linking inapplicable | None for classification; runtime loading unvalidated |
| OVY_127 | 0 | None | ID/file 127; After ds_protect; 32-byte padding image | Metadata | E | Verified empty; linking inapplicable | None for classification; runtime loading unvalidated |
| OVY_128 | 0 | None | ID/file 128; After ds_protect; 32-byte padding image | Metadata | E | Verified empty; linking inapplicable | None for classification; runtime loading unvalidated |

## Accounting and validation

The original 132 identities remain available in `images.json` and the full graph
report. Ten verified empty identities leave 122 original nonempty images. Four
special core identities (`main`, `ds_protect`, `ITCM`, `DTCM`) are reported
individually; the ordinary nonempty overlay denominator is 118. Counts for linked
nonempty images, nonempty images not linked, verified empties, unverified empty
metadata and linked images lacking full runtime validation are separate.
The legacy `empty_original_images` field remains a raw memberless-manifest count;
only `verified_empty_original_identities` claims independent verification.

`heartgold_image_report` regenerates current artifact-backed counts and freshness
status. An existing stale dylib is not a current successful link. Binding checks
and unchanged native-overlay preflight do not establish complete runtime support.

Measured with the existing `build/` configuration after rebuilding the selected
noncore images:

- **95 linked nonempty images**, all ordinary overlays; **10 verified empty
  identities**; **27 nonempty identities not fully linked** by the artifact report.
- Core status: `main`, `ITCM`, `DTCM` absent; `ds_protect` reports incomplete
  original membership (its existing approved native replacement links and passes
  preflight, but is not credited as a complete original-member image).
- All 95 credited links remain short of full runtime validation. The extra
  `ds_protect` artifact explains the 96 successful binding/preflight checks;
  it does not change the 95 complete original nonempty image count.
- Configuration succeeded. All **96 selected noncore image targets** built;
  all passed unchanged native-overlay preflight. No newly nonempty image was
  discovered or added. Build log: `build/independent-empty-noncore-build.log`;
  preflight log: `build/independent-empty-preflight.log`.
- Six relevant CTest entries passed: linker contracts, overlay manifest,
  overlay bindings, image graph, provider registry and link evidence. The graph
  suite covers all ten IDs, native selection rejection, missing declaration and
  checksum evidence, ID/placement changes and accounting without empty inflation.
  Log: `build/independent-empty-tests.log`.
- An initial broad image-target rebuild failed at OVY_44 on original unresolved
  `DWC_ProcessFriendsMatch`/`WifiConnection_*` providers. The closure is unchanged;
  that failure remains visible in `build/independent-empty-build.log`. No full
  game link or runtime execution is claimed.
- `upstream/pokeheartgold` remained completely clean at pinned commit
  `6d94f9137ced9db12d9ce827a8127c97b779bbeb`. No core-closure implementation,
  guest32 infrastructure or linker/preflight rules changed. No commit or push.

The graph report in `build/native-graph/report/` contains the full 132-identity
inventory, ownership, original-member lists and measured counts. These counts are
specific to that artifact inventory; supplemental inventories can change observed
member coverage, and should be supplied consistently for comparisons.
