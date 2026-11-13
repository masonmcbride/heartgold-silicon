# Source-owned WM/WVR/DWC providers.
# This compatibility module replaces historical archive paths.
# Remove this transitional file once the production link is validated.

set(HEARTGOLD_WIRELESS_SHADOW ON)
include("${CMAKE_CURRENT_LIST_DIR}/wireless_shadow.cmake")

target_link_libraries(heartgold PRIVATE
    heartgold_wm_core_native_original
    heartgold_wm_native_candidates
    heartgold_wvr_original
)

# Preserve the existing native gWmWork owner.
target_link_options(hg_wm_arm9 PRIVATE
    "LINKER:-exported_symbol,_gWmWork")

target_link_libraries(heartgold PRIVATE
    heartgold_wm_original_work_storage
    heartgold_wm_original_scalar_storage
)

target_link_libraries(heartgold PRIVATE
    heartgold_dwc_original_typed_storage
)
