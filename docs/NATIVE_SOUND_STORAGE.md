# Native NitroSystem assembly storage

Both objects occur in the static main image in `main.lsf`. Only labels with
actual storage in these objects are owners or aliases; `.public` alone does
not allocate anything. The generator checks each original object's full digest
and extracts owner declarations from the original sound headers. One generated
C translation unit per original assembly input lives under the binary directory.
Clang inline assembly immediate operands expand `offsetof` directly into Mach-O
`.set` aliases; no numerical native offsets are maintained. C ownership macros
also expose the overlap to the optimizer. Player view types retain the native
`sizeof(SndPlayerInfo)` stride and permit aliasing of the underlying members.

## Complete label inventory

ARM32 offsets below document original ownership only, never native allocation.

| Object / label | ARM32 offset | Ownership / native handling |
| --- | ---: | --- |
| `nnsys_g3d_snd_bss.s: gCurrentRenderState` | `0x0` | independent G3dRS pointer; graphics translation deferred |
| `nnsys_g3d_snd_bss.s: gMatAnmResultBuffer` | `0x4` | independent G3dMatAnmResult[64]; graphics translation deferred |
| `nnsys_g3d_snd_bss.s: gScaleCache` | `0xE04` | independent G3dScaleCacheEntry array; graphics translation deferred |
| `nnsys_g3d_snd_bss.s: gScaleCacheScaleY` | `0xE08` | member label in preceding graphics owner; graphics translation deferred |
| `nnsys_g3d_snd_bss.s: gScaleCacheScaleZ` | `0xE0C` | member label in preceding graphics owner; graphics translation deferred |
| `nnsys_g3d_snd_bss.s: gScaleCacheInvScale` | `0xE10` | member label in preceding graphics owner; graphics translation deferred |
| `nnsys_g3d_snd_bss.s: gScaleCacheInvScaleY` | `0xE14` | member label in preceding graphics owner; graphics translation deferred |
| `nnsys_g3d_snd_bss.s: gScaleCacheInvScaleZ` | `0xE18` | member label in preceding graphics owner; graphics translation deferred |
| `nnsys_g3d_snd_bss.s: gEvpMtxCache` | `0x1404` | independent G3dEvpMtxCache[64]; graphics translation deferred |
| `nnsys_g3d_snd_bss.s: gEvpMtxCacheFirstDirMtx` | `0x1444` | member label in preceding graphics owner; graphics translation deferred |
| `nnsys_g3d_snd_bss.s: gGeBufferState` | `0x2D04` | independent G3dGeBufferState; graphics translation deferred |
| `nnsys_g3d_snd_bss.s: gGeBufferStateIsLocked` | `0x2D08` | member label in preceding graphics owner; graphics translation deferred |
| `nnsys_g3d_snd_bss.s: gSndMainState` | `0x2D20` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndMainPreSleepCallback` | `0x2D30` | alias of `gSndMainState.preSleep` |
| `nnsys_g3d_snd_bss.s: gSndMainPostSleepCallback` | `0x2D3C` | alias of `gSndMainState.postSleep` |
| `nnsys_g3d_snd_bss.s: gSndDriverInfo` | `0x2D60` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndResourceMgr` | `0x5120` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndWaveOuts` | `0x512C` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndFreeSeqPlayerList` | `0x526C` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndSeqPlayerPrioList` | `0x5278` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndSeqPlayers` | `0x5284` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndPlayerInfo` | `0x56C4` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndPlayerInfoNumPlaying` | `0x56CC` | alias of `gSndPlayerInfo[0].playerList.numObjects` |
| `nnsys_g3d_snd_bss.s: gSndPlayerInfoPlayableSeqCount` | `0x56DC` | alias of `gSndPlayerInfo[0].playableSeqCount` |
| `nnsys_g3d_snd_bss.s: gSndPlayerInfoAllocChBitFlag` | `0x56E0` | alias of `gSndPlayerInfo[0].allocChBitFlag` |
| `nnsys_g3d_snd_bss.s: gSndPlayerInfoVolume` | `0x56E4` | alias of `gSndPlayerInfo[0].volume` |
| `nnsys_g3d_snd_bss.s: gSndStrmListInitialized` | `0x5B44` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndStrmList` | `0x5B48` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndStrmCallbackBuffers` | `0x5B54` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndStrmChannels` | `0x5B94` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndCaptureWork` | `0x5C14` | typed independent object |
| `nnsys_g3d_snd_bss.s: gSndCaptureMsgQueue` | `0x5C1C` | alias of `gSndCaptureWork.msgQueue` |
| `nnsys_g3d_snd_bss.s: gSndCaptureState` | `0x5C5C` | alias of `gSndCaptureWork.state` |
| `nnsys_g3d_snd_bss.s: gSndCurrentArc` | `0x6210` | typed independent object |
| `nnsys_snd_arc_strm_bss.s: _021E0950` | `0x0` | typed independent object |
| `nnsys_snd_arc_strm_bss.s: gSndArcStrmFreeCommandList` | `0xC` | typed independent object |
| `nnsys_snd_arc_strm_bss.s: gSndArcStrmMutex` | `0x678` | typed independent object |
| `nnsys_snd_arc_strm_bss.s: gSndArcStrmCommandList` | `0x690` | typed independent object |
| `nnsys_snd_arc_strm_bss.s: gSndArcStrmPlayers` | `0x69C` | typed independent object |

## Explicit unresolved storage questions

- `gSndArcStrmFreeCommandList` consumes 0x66C bytes before the next label;
  its declared ARM32 NNSFndList accounts for 0xC. The remaining unnamed
  0x660 bytes have no safe declared owner in the available C source. Only the
  list is translated. An archive command pool/type/count must be established
  from original initialization code before this region can be translated.
- The 0x40-byte main-state interval exceeds its ARM32 C type (0x28),
  and the geometry-state interval also contains trailing untyped bytes.
  Those tails are not inferred to be C members or allocated as guessed objects.
- `gSndWaveArcHeader` is public-only here, without a label or allocation in
  either object. Its declaration is not evidence of storage ownership here.
- Other `.public` declarations after the archive-stream storage refer to symbols
  defined elsewhere; they are not independent allocations in this object.
- Archive stream/player/capture types contain original opaque byte regions. Their
  declared fields are compiled with native pointer width; interpreting those opaque
  regions as additional native objects remains unsupported. This does not establish
  sound runtime support or solve serialized wave pointer storage.

The graphics label groups are inventoried but deliberately not implemented by
this sound task. No upstream file or libntr checkout is modified.
