# Canonical source-owned WM/WVR/DWC libraries.
set(_hg_wireless_sources
    "${PROJECT_SOURCE_DIR}/hardware_drivers/wireless")
set(_hg_wireless_output
    "${PROJECT_BINARY_DIR}/wireless-shadow")

function(_hg_wireless_library name)
    add_library(${name} STATIC EXCLUDE_FROM_ALL ${ARGN})
    set_target_properties(${name} PROPERTIES
        ARCHIVE_OUTPUT_DIRECTORY "${_hg_wireless_output}")
    target_compile_definitions(${name} PRIVATE
        "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
    target_include_directories(${name} PRIVATE
        "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
    target_compile_options(${name} PRIVATE
        "$<$<COMPILE_LANGUAGE:C,CXX>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>")
    target_link_libraries(${name} PRIVATE nitro_config)
    add_dependencies(${name} heartgold_native_headers fx_constants)
    if(TARGET heartgold_overlay_native_sources)
        add_dependencies(${name} heartgold_overlay_native_sources)
    endif()
endfunction()


_hg_wireless_library(heartgold_wm_core_native_original
    "${_hg_wireless_sources}/wm_core_native_adapted.c")

_hg_wireless_library(heartgold_wm_native_candidates
    "${game_source}/lib/NitroSDK/src/wm_requests.c"
    "${game_source}/lib/NitroSDK/src/wm_settings.c")

_hg_wireless_library(heartgold_wvr_original
    "${_hg_wireless_sources}/wvr_native_adapted.c"
    "${_hg_wireless_sources}/wvr_native_state.c")

_hg_wireless_library(heartgold_wm_original_work_storage
    "${_hg_wireless_sources}/wm_native_work_storage.c")

_hg_wireless_library(heartgold_wm_original_scalar_storage
    "${_hg_wireless_sources}/wm_original_scalar_storage.c")

_hg_wireless_library(heartgold_dwc_original_typed_storage
    "${_hg_wireless_sources}/dwc_original_typed_storage.c")

# Preserve the original tentative-definition/common-symbol linkage.
target_compile_options(heartgold_dwc_original_typed_storage
    PRIVATE -fcommon)

