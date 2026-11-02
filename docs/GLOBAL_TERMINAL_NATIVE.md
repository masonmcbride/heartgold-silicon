# OVY_39 / OVY_40 native integration

**The requested two-image completion criterion is not met.** OVY_40 now links as
an actual native ARM64 dylib. OVY_39's complete five-member archive builds, its
data and ABI tests pass, but its dylib still fails on 21 real imports owned by
OVY_0. No OVY_39 dylib is present. No runtime networking execution is claimed.

## Implemented ownership and build integration

`cmake/native_overlays.cmake` selects OVY_39, OVY_40 and OVY_41 through the existing
manifest selector. No generated selection or provider files were manually edited.
OVY_39 retains all three original C members and both assembly-data members.
OVY_40 retains all twenty C members and the existing VS Recorder data conversion,
with one data definition producer. OVY_41 retains its original members. The
original `After OVY_38`, `After OVY_39` and `After OVY_40` relationships remain in
selection/registry metadata; cross-image imports are independently derived from
actual archive exports. In particular, the real OVY_39-to-40 reverse references
are not erased to turn the placement chain into a false link dependency order.

Both new data recipes use `cmake/native_assembly_data.py`, with their strict
parser/validator in `tests/global_terminal_data_validation.py`. Original assembly and
consumer hashes are checked. Numeric `.byte` and `.word` contents remain exact;
`.rodata`, `.data` and `.bss` map to Mach-O `__TEXT,__const`, `__DATA,__data` and
zero-fill `__DATA,__bss`. Original public/local label visibility is retained.
The unused background table remains present. Both `sGlobalTerminalServerCommandIds`
and `_0222A9AC` label the same bytes at offset zero, without a second allocation.
Custom commands declare outputs, original inputs, consumers and helper scripts.
The existing VS Recorder helper is now also an explicit generation dependency.

The nine missing SOC entry points now have their genuine original main-image
providers: `lib/NitroWiFi/src/soc.c`, `soc_inet.c` and `soc_gethostbyname.c`.
Main selection validates their original `main.lsf` membership. These are the
original SDK algorithms, not POSIX substitutes or success shims. The socket consumer now uses their canonical `SocAddress`, `SocInAddr` and
`SocHostEnt` declarations: the old opaque four-byte host-entry field represents
two 16-bit fields, not an eight-byte pointer. The native address-list offset is
checked at 24, IPv4 structures remain 8/4 bytes, and the connect call supplies the
SDK's length parameter. These are declaration/calling-ABI adaptations through
`native_sources.py`, not replacement socket algorithms. Their downstream
SOCL implementation and runtime behavior are not established by this work.

OVY_40's actual native image is:

```
build/native-overlays/libheartgold_image_40.dylib
```

Its two-level imports bind `GlobalTerminalNet_*` to image 39 and the imported
OVY_41 `AccessoryPortrait_*` functions to image 41. The main-owned
`AccessoryPortrait_LaunchApp` wrapper keeps its main ownership. The binding
contracts come from strong definitions in the actual archives, not invented
exports. The missing image 39 still prevents treating image 40 as loadable in a
complete application. An intermediate interface file is not reported as an
implemented image 39.

## Socket storage ABI

The original assembly does **not** allocate independent socket, host and settings
objects. `GlobalTerminalSocket` begins at the socket label and extends through
the settings reservation. The hostname and settings are interior aliases.
`sizeof(GlobalTerminalSocketSettings)` is 0x42, even though the original assembly
reserves 0x74 at that label. Shrinking that reservation to the settings type's
size would overwrite the remaining socket fields and following thread.

Offsets relative to `sGlobalTerminalSocket` are:

| Label / boundary | Original DS | Native ARM64 |
| --- | ---: | ---: |
| Socket / `ov39_0222AB8A` | 0 / 0x6 | 0 / 0x6 |
| Hostname view | 0x140 | 0x140 |
| Settings view | 0x200 | 0x200 |
| Shared port | 0x240 | 0x240 |
| Thread | 0x274 | 0x280 |
| Mutex | 0x334 | 0x428 |
| Downward stack start | 0x34c | 0x460 |
| Exported stack end | 0xb4c | 0xc60 |
| End of trailing reservation | 0xb5c | 0xc70 |

Only three BSS extents grow:

* Settings reservation: 0x74 to 0x80, because the *enclosing socket* grows from
  0x274 to 0x280 through its two full-width request/response pointers and padding.
  The settings view, shared port and all earlier aliases keep their offsets.
* Thread: 0xc0 to 0x1a8, matching the selected real native `OSThread`, alignment 8.
* Mutex-plus-stack: 0x818 to 0x838. The native `OSMutex` takes 0x38 bytes; the
  original downward stack remains **exactly 0x800 bytes** immediately after it.

The final 0x10 bytes following the exported stack-end symbol are retained.
The native BSS base has alignment 16. Its actual offsets align both the stack
start and end to 16 without extra padding between mutex and stack. Original
initialized sections retain alignment 4. Generated consumer assertions check
`sizeof`, alignment and alias offsets using the original private C declarations
and selected SDK headers. An SDK ABI change fails the build instead of silently
changing the reservation or accepting stale numeric sizes.

The fork's `OS_CreateThreadReal` previously truncated the supplied native stack
address to 32 bits when recording `stackTop` and `stackBottom`. Those two metadata
assignments now retain full-width addresses under `SDK_PORT`; the original DS
branch is unchanged. The change is in `upstream/libntr` and is mirrored into the
already-selected local review checkout, preserving its other changes. Pins and
HEADs are unchanged; nothing was committed or published.

## Validation

The focused positive run passed four tests: `os_init`,
`global_terminal_native_layout`, `global_terminal_native_data` and
`global_terminal_native_image40`.

The layout executable compiles the actual adapted original socket consumer,
checks original ID-table bytes and both labels, hostname/port aliases, all
adjacent native object boundaries, and the 0x800-byte stack. Under ASan/UBSan it
checks the original stack-clear primitive's endpoint behavior, invokes the real
native mutex initializer and the real pthread-backed SDK thread creation, and
verifies stack metadata above 4 GiB. Its test thread uses `pthread_exit` after the
creation checks, deliberately avoiding the separately unsupported SDK
context/scheduler exit path. This is not validation of SDK context switching,
thread kill, networking or the original socket worker's runtime behavior.

The independent object validator checks every original initialized byte, all
label offsets (including the coincident command labels), native storage extents,
section sizes/alignment and absence of unexpected relocations. Negative checks
corrupt command bytes and move the command alias in a real Mach-O nlist, requiring
both to be rejected. The image test checks the real ARM64 Mach-O dylib header,
strong exports, two-level imports and original owning images, no dynamic lookup,
preflight constraints, and all 129 reused VS Recorder data relocations.

The strict `global_terminal_native_images` test requires successful actual links
of both images. It currently **fails** at the real OVY_39 linker. It is not
silently skipped or changed to expect success while image 39 is absent.

Commands and evidence:

```
cmake -S . -B build
cmake --build build --target test_global_terminal_layout heartgold_image_40 -j8
ctest --test-dir build -R 'global_terminal_native_(layout|data|image40)$|os_init' --output-on-failure
cmake --build build --target heartgold_image_39 -j8  # fails: real OVY_0 providers absent
ctest --test-dir build -R '^global_terminal_native_images$' --output-on-failure
```

Artifacts are under `build/global-terminal-integration/`: `data.json`,
`image-40.json`, `tests.log`, `image-39.log`, `images-test.log` and
`provider-blockers.json`. All generated code, test binaries and evidence remain
inside the selected binary directory. Original HeartGold is unchanged and clean.

## Remaining blocker

All 21 remaining imports belong to OVY_0. That original image has 42 C members
and four assembly-data members, and is not a selected complete native image.
The four missing native data recipes are `lib/NitroDWC/asm/dwc_lib_rodata.o`,
`lib/NitroDWC/asm/dwc_lib_data.o`, `lib/NitroDWC/asm/dwc_lib_bss.o` and
`lib/NitroDWC/asm/dwc_gamespy_bss.o`. Its strong functions cannot be relabeled as main or OVY_39 definitions, nor can
an export-only interface be supplied without actual native providers. Completing
its native data/provider closure remains unimplemented here. This is real
remaining work, not successful completion of the assignment.

The following exact symbols are from the actual OVY_39 linker diagnostic:

| Undefined symbol | Genuine original provider | Owning image |
| --- | --- | --- |
| `_DWC_Alloc` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_CheckInet` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_CleanupInet` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_ClearError` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_ConnectInetAsync` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_Free` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_GetApInfo` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_GetInetStatus` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_GetLastError` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_GetLastErrorEx` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_InitInetEx` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_NASLoginAsync` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_NASLoginProcess` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_ProcessInet` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_SVLGetTokenAsync` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_SVLProcess` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_SetAuthServer` | `lib/NitroDWC/src/net_common.c` | OVY_0 |
| `_DWC_ShutdownFriendsMatch` | `lib/NitroDWC/src/dwc_main.c` | OVY_0 |
| `_DWC_ShutdownGHTTP` | `lib/NitroDWC/src/ap_connect_control.c` | OVY_0 |
| `_WifiConnection_ClassifyErrorCode` | `src/wifi_connection.c` | OVY_0 |
| `_gsSocketInetAddr` | `lib/NitroDWC/src/gp_api.c` | OVY_0 |
