# Runtime defect patterns for the native diagnostic

These are observed defect classes and acceptance cases for a future general
diagnostic. This list is not evidence that an automatic detector exists or that
the entire game is verified. Compare original sources with the selected native
production inputs; do not flag already-corrected generated code as unresolved.

See [FIELD_ENTRY_AUDIT.md](FIELD_ENTRY_AUDIT.md) for the scoped field-entry review,
additional graphics-loader bypasses, negative findings and remaining limits.

| Pattern | Observed example | Required diagnostic |
| --- | --- | --- |
| Serialized and native layouts confused | Oak palette; text font-focus NCGR | Follow file bytes into pointer-bearing structs; check fixed offsets, native pointer widths and ownership. |
| Required side effects removed by build configuration | Sprite registration inside `GF_ASSERT` | Compare original required definitions and compiled call presence. |
| Incomplete asset-layout support | Name-entry standard NCER cells | Compare actual asset attributes with decoder branches and native indexing strides. |
| Native address narrowed | Timer3 register read through `u32` | Track address loss through pointer/integer conversions. |
| Interior resource pointer narrowed during lookup | Shadow material alpha: `GetDictData2` and `GetMatData2` | Preserve native base/entry pointers while retaining 32-bit serialized offsets. Exercise material mutations as well as texture-name lookup. Both functions appeared in the initial diagnostic's narrowing inventory before this runtime trace. |
| Hardware layout assumed for host variables | SDK timer setters | Check register identity; independent mapped variables do not form a hardware register array. |
| Allocation/initialization extent disagrees with native consumers | Map render objects, pointer tables and animation pools | Relate allocation, clearing, indexing and variable tails to their native types. |
| Outer `sizeof` hides an undersized embedded object | `MapObjectManager`'s DS-sized renderer reservation overwritten by native `MapObjectRender` | Follow interior pointers into typed consumers; validate embedded size and alignment as well as outer allocation. Embed the actual type and check adjacent members through real accessors. |
| Non-void function falls through with a consumed result | `MapPropAnimationPoolList_New` -> `AreaMapAnimation_New` -> `MapPropAnimationPoolList_AddPool` | Diagnose reachable missing returns (`-Wreturn-type`) and identify callers consuming the undefined result. This is C undefined behavior, not exclusively a 32/64-bit defect. |
| Hardware interrupt progress reduced to frame-loop progress | VBlank queue reaches 32/32 during `Footprints_LoadModels`; later billboard transfer task is NULL at map teardown | Check producers against interrupt-delivery opportunities during long operations, not only queue capacity. SDK main-thread safe points deliver due VBlank with interrupt masks and a recursion guard; worker threads cannot dispatch it. The new regression must pass before considering the runtime fix verified. |
| Host-only early return leaks a saved interrupt mask | `OS_GetTick` disables IRQs, then returns from `SDK_PORT` without restoring; `NitroMain` calls it just before the overlay manager | Check all platform-specific return paths for balanced state restoration. Clock reads must preserve both enabled and disabled caller states. Also verify frame delivery has one owner, not duplicate dispatch in `SIM_Render` and `OS_WaitIrq`. |

The missing-return case escaped the earlier allocation regression because the
fixture constructed a valid list on its stack and called `AddPool` directly.
The maintained regression now invokes the original generated list constructor,
checks that its result is the actual allocation and is fully initialized, then
adds two pools through that returned pointer. Extracted production constructors
are compiled with `-Werror=return-type` and exercised under ASan/UBSan.

Future diagnostic acceptance must include historical bad inputs and corrected
native inputs, plus known-correct fixed-width asset buffers as negative controls.
Record automatic findings, manual findings and misses separately; matching a
known filename is not proof of a general rule. No single confirmed defect proves
the cause of every later crash in its subsystem.
