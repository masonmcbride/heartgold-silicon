# Field-entry source audit

Scope: Oak's application exit, new-game state initialization, `FieldMap_Init`,
the field manager/resource setup, `FieldMap_Main`/`FieldMap_UpdateFrame`, and
associated render/task callbacks. This is a source review, not a successful
house-entry trace or a proof that every dynamic path is safe. Builds, tests and
runtime verification remain user-run.

## Transition and first-frame review

| Boundary reviewed | Representation checks and observations |
| --- | --- |
| Oak -> game-state initialization | Naming argument ownership and overlay handoff; previously corrected Timer3 register access starts play time. |
| `FieldMap_Init` | Reset/load/bottom-screen/done stages, field heap ownership, resource creation order, VBlank registration. |
| `InitGraphicsAndManagers` | Area-data models, typed render objects/pointer tables, preload IDs, returned animation-list owner, variable animation extents. Earlier fixes remain required. |
| Area/map resources | `area_data.c`, `map_prop_manager.c`, `map_prop_animation.c`, `resource_bank.c`: native allocations versus serialized model/prop IDs and fixed-width offsets. |
| Map and collision loading | `map_load_manager.c`, `map_load_buffers.c`, `bdhc.c`, `dynamic_terrain_height.c`: owned buffers, numeric file headers, counts and pointer views. Numeric file records remain fixed-width. |
| Effects and map objects | `field_effect_manager.c`, `field_3d_object_task.c`, `map_object.c`, `map_object_models.c`, `map_object_billboard_motion.c`, `map_object_render.c`: callback state, array extents, embedded renderer storage, actual owner/accessor chain. |
| Shadows/reflections and model helpers | `field_shadow.c`, `field_reflection.c`, `render_model.c`, `render_animation.c`, `g3d_model.c`: resource lifetimes and material dictionary pointers. The recently corrected material helpers remain required. |
| Billboard resources/tasks | `billboard_lists.c`, `billboard_gfx_sequence.c`, renderer load/create/transfer/release tasks: typed arrays and explicit decoding of numeric sequence data. |
| Camera/environment/UI entry | Camera shift, area lighting, weather, signposts, bottom-screen dispatch, HBlank setup and first-frame update ordering. Graphics bypasses below were found. |

## Additional source-proven graphics bypasses corrected

All five sites previously passed original file bytes to unpackers that interpret
pointer-bearing DS records using native layout. The shared native character and
palette getters already implement the required decoding and single-owner
lifetime. Route these callers through those getters; retain original archive
members, copy sizes, rendering calls and frees.

| Caller | Correction | Trigger to watch during runtime |
| --- | --- | --- |
| `LoadMapSignpostFrameAndGraphic` | Shared palette getter for `a/0/3/6` member 1 | Signpost/map dialog frame rendering. |
| `TouchscreenListMenuSpawner_Create` | Shared character and palette getters; preserve both owners until destroy | Field/script touchscreen selection menu creation. |
| `WeatherSystem_LoadBgPalette` | Shared open-NARC palette getter | Weather mode with BG palette data. |
| `WeatherSystem_LoadBgChars` | Shared open-NARC character getter | Weather mode with BG character data. |

These may occur after leaving the first room. They are not predictions that the
very next house-entry failure must be one of these functions. The maintained
native source tests retain exact expected adaptations and source-drift checks;
the native-data fixture exercises the common decoded owners with real assets.

## Findings deliberately not treated as new defects

- BDHC/map headers and prop archive records contain fixed-width numeric data;
  replacing their file extents with expanded native storage would be incorrect.
- The billboard queue reserves twice the pending-array size for its transfer
  array. The native pending record is larger than the transfer record; that
  reservation is sufficient, not an undersized pointer array.
- `AreaDataManager_TrimTextureFile` subtracts two narrowed addresses within the
  same allocation. For the bounded resource size, unsigned modulo subtraction
  preserves their distance. It merits cleanup but is not the same as dereferencing
  a truncated pointer.
- `EmoteBubble_Show` has a missing return on its successful path, but the current
  caller discards its result. Record it for return-contract cleanup rather than
  claiming it explains the reported crash.

## Remaining limits

### Main-loop follow-up

Reviewed `NitroMain`'s overlay/task ordering, its two clock reads, RTC update,
IGT update, buffer swap request, print queue, frame wait, brightness/fade update,
registered frame callback, sound-update boundary and VWait queue. Additional
source checks covered `system.c`, `sys_task.c`/`sys_task_api.c`, `gf_rtc.c`,
`brightness.c`, `screen_fade.c`, `screen_fade_effects.c`,
`swap_3d_buffers.c`, `igt_counter.c`, `timer3.c`, `heap.c`, SDK arena allocation
and SDK interrupt/clock return paths. This is targeted review of state, storage,
returns and ownership, not line-by-line proof of every downstream SDK service.

New correction: all four `InitSystemForTheGame` task arenas now request
`_Alignof(SysTaskQueue)` instead of 4. The heap's pointer-table reservation now
requests `_Alignof(NNSFndHeapHandle)`. The previously captured VBlank arena
address was four bytes off an eight-byte boundary. The SDK arena allocator
honors the requested alignment; it did not repair the caller's DS assumption.
The native loading regression now deliberately starts the arena misaligned and
allocates the queue using its actual alignment. Source tests also cover the
four production startup calls. These changes have not been built/tested here.

Not widened: the async-save marker is genuinely one `u32`; the swap-request
record contains numeric enum/BOOL fields; the RTC work contains numeric date/time
records, not serialized native pointers. No game timing or input algorithm was
replaced during this review.

The latest user trace still passes NULL to `SysTask_Destroy` from
`MapObjectRender_DestroyQueue` when leaving the room, even with the clock restore
present in the inspected executable. Current queue/scheduling behavior therefore
remains unresolved; the new alignment correction is not claimed to explain it.

Rendering follow-up: `AreaDataManager` enables edge marking and sets the DS edge
table, but `hardware_drivers/metal/g3_metal.mm` has no corresponding edge-table
input or edge-marking pass. Missing outlines are a renderer feature gap. The
intermittent clock line has not been attributed to one proven cause. Changing
depth comparison, geometry or camera parameters without evidence would be a
different kind of workaround and has not been done.

See [NATIVE_RUNTIME_PATTERNS.md](NATIVE_RUNTIME_PATTERNS.md) for the chronological
failure trail and the distinction between corrected, user-observed and unresolved
cases.

A later runtime capture found the VBlank queue at 32/32 during
`Footprints_LoadModels`. The source-only entry review did not prove scheduling
progress during synchronous loading. The SDK now includes cooperative due
VBlank delivery at interrupt-restore boundaries on the frame thread, and
restores the caller's interrupt mask when returning from the native
`OS_WaitIrq` frame path. This does not add worker-thread IRQ execution or increase
queue capacity. `native_vblank_loading` checks the original 32-entry queue with
76 tasks, nested masking, worker exclusion, recursion and wait restoration.
Build/test and visual runtime results remain pending user validation.

The subsequent capture still showed 32/32 with CPSR IRQ mask `0x80`. Source and
linked-code inspection identified `OS_GetTick` as a returning clock function
that called `OS_DisableInterrupts` without restoring on its `SDK_PORT` branch.
`NitroMain` calls it immediately before `Main_RunOverlayManager`, so the first
safe-point change alone could not deliver loading IRQs. The fork now restores
the clock caller's saved mask. The regression reproduces the clock reads before
overlay-style work, checks clock reads while masked, and queues work drained by
enabled clock-read safe points without a frame wait. The selected
`os_irqHandler.c` also relinquishes its legacy extra callback because
`SIM_Render` owns the frame-boundary dispatch; the regression checks exactly
one callback at `OS_WaitIrq`. These new checks have not been run by the agent.

Indirect callbacks, script-driven application launches, conditional weather and
map-specific data expand execution beyond the entry path. Existing source/IR
diagnostic inventories are candidates, not a complete automatic proof. Direct
unpacker callers elsewhere (for example Pokémon portrait utilities) remain for
a later subsystem audit; this change does not claim all graphics decoding is
repaired. CARD synchronization and full save/load behavior are also not proved
by this source review.
