# Source-built provider comparison. Not linked into the canonical executable.
option(HEARTGOLD_WIRELESS_SHADOW
    "Build WM/WVR/DWC replacement archives for ABI comparison" OFF)

if(HEARTGOLD_WIRELESS_SHADOW)
    if(NOT TARGET heartgold_main)
        message(FATAL_ERROR
            "HEARTGOLD_WIRELESS_SHADOW requires HEARTGOLD_BUILD_GAME=ON")
    endif()

    set(_hg_wireless_sources
        "${PROJECT_SOURCE_DIR}/native-adaptations/wireless")
    set(_hg_wireless_output
        "${PROJECT_BINARY_DIR}/wireless-shadow")
    set(_hg_shadow_targets)

    function(_hg_wireless_shadow name)
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
        set(_hg_shadow_targets
            "${_hg_shadow_targets};${name}" PARENT_SCOPE)
    endfunction()

    foreach(_hg_required
            wm_core_native_adapted.c
            wvr_native_adapted.c
            wvr_native_state.c
            wm_native_work_storage.c
            wm_original_scalar_storage.c
            dwc_original_typed_storage.c)
        if(NOT EXISTS "${_hg_wireless_sources}/${_hg_required}")
            message(FATAL_ERROR
                "Recovered provider missing: ${_hg_required}")
        endif()
    endforeach()

    _hg_wireless_shadow(heartgold_wm_core_native_original
        "${_hg_wireless_sources}/wm_core_native_adapted.c")

    _hg_wireless_shadow(heartgold_wm_native_candidates
        "${game_source}/lib/NitroSDK/src/wm_requests.c"
        "${game_source}/lib/NitroSDK/src/wm_settings.c")

    _hg_wireless_shadow(heartgold_wvr_original
        "${_hg_wireless_sources}/wvr_native_adapted.c"
        "${_hg_wireless_sources}/wvr_native_state.c")

    _hg_wireless_shadow(heartgold_wm_original_work_storage
        "${_hg_wireless_sources}/wm_native_work_storage.c")

    _hg_wireless_shadow(heartgold_wm_original_scalar_storage
        "${_hg_wireless_sources}/wm_original_scalar_storage.c")

    _hg_wireless_shadow(heartgold_dwc_original_typed_storage
        "${_hg_wireless_sources}/dwc_original_typed_storage.c")

    # Preserve the original tentative-definition/common-symbol linkage.
    target_compile_options(heartgold_dwc_original_typed_storage
        PRIVATE -fcommon)

    add_custom_target(heartgold_wireless_shadow
        DEPENDS ${_hg_shadow_targets})
endif()
