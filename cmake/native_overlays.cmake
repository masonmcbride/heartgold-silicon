# Explicitly selected local-fork integration; preserve original image membership.
enable_language(ASM)
# The same declared-output generator handles static and overlay data members.
include("${PROJECT_BINARY_DIR}/native-graph/main-data.cmake")
target_sources(heartgold_main PRIVATE ${hg_main_data_sources})
find_program(HG_NATIVE_OTOOL NAMES otool REQUIRED)
set(HEARTGOLD_NATIVE_EXTRA_OVERLAYS "" CACHE STRING "Explicit additional original overlay names")
set(hg_overlay_manifest "${CMAKE_CURRENT_LIST_DIR}/native_overlay_manifest.py")
set(overlay_link_dir "${PROJECT_BINARY_DIR}/native-overlays")
set(hg_overlay_select --supported --select OVY_36 --select intro_title --select OVY_62 --select ds_protect --select OVY_39 --select OVY_40 --select OVY_41)
target_sources(heartgold_main PRIVATE "${PROJECT_SOURCE_DIR}/hardware_drivers/graphics/nsbta_callback.c")
foreach(name IN LISTS HEARTGOLD_NATIVE_EXTRA_OVERLAYS)
    list(APPEND hg_overlay_select --select "${name}")
endforeach()
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${hg_overlay_manifest}" "${CMAKE_CURRENT_LIST_DIR}/native_assembly_data.py"
    "${CMAKE_CURRENT_LIST_DIR}/native_image_graph.py" "${CMAKE_CURRENT_LIST_DIR}/native_data_ir.py"
    "${CMAKE_CURRENT_LIST_DIR}/native_abi.py"
    "${CMAKE_CURRENT_LIST_DIR}/native_data_layouts.py" "${CMAKE_CURRENT_LIST_DIR}/native_data_layouts.json"
    "${CMAKE_CURRENT_LIST_DIR}/native_image_policy.json")
execute_process(COMMAND "${Python3_EXECUTABLE}" -B "${hg_overlay_manifest}"
    --game "${game_source}" --adapted-dir "${native_root}" --out "${overlay_link_dir}" ${hg_overlay_select}
    COMMAND_ERROR_IS_FATAL ANY)
include("${overlay_link_dir}/selection.cmake")
if("45" IN_LIST hg_selected_overlay_ids)

# HEARTGOLD_OVY45_NATIVE_SOURCE_OVERRIDE
# Retain pristine pinned source; compile this explicitly reviewed
# native ABI adaptation for OVY_45 only.
set(_hg_ovy45_adaptation
    "${CMAKE_SOURCE_DIR}/native-adaptations/OVY_45/lobby_chat_remove_channel.cpp"
)
if(NOT EXISTS "${_hg_ovy45_adaptation}")
    message(FATAL_ERROR "OVY_45 native C++ adaptation is missing")
endif()
set(_hg_ovy45_original_found FALSE)
foreach(_hg_ovy45_source IN LISTS hg_overlay_45_sources)
    if("${_hg_ovy45_source}" MATCHES
       "(^|/)src/lobby/lobby_chat_remove_channel[.]cpp$")
        list(REMOVE_ITEM hg_overlay_45_sources "${_hg_ovy45_source}")
        list(APPEND hg_overlay_45_sources "${_hg_ovy45_adaptation}")
        set(_hg_ovy45_original_found TRUE)
    endif()
endforeach()
if(NOT _hg_ovy45_original_found)
    message(FATAL_ERROR
        "OVY_45 source override failed: original member not located"
    )
endif()
endif()

set(overlay_archives)

# HEARTGOLD_OVY45_NATIVE_GET_WORK_WRAPPER
# Select the original C implementation through a native-only
# translation-unit wrapper; leave the pinned checkout untouched.
if("45" IN_LIST hg_selected_overlay_ids)
    set(_hg_ovy45_get_work_original_found FALSE)
    foreach(_hg_ovy45_source IN LISTS hg_overlay_45_sources)
        if("${_hg_ovy45_source}" MATCHES
           "(^|/)src/lobby/ppw_lobby_get_work[.]c$")
            list(REMOVE_ITEM hg_overlay_45_sources "${_hg_ovy45_source}")
            list(APPEND hg_overlay_45_sources
                "${CMAKE_SOURCE_DIR}/native-adaptations/OVY_45/ppw_lobby_get_work_native.c")
            set(_hg_ovy45_get_work_original_found TRUE)
        endif()
    endforeach()
    if(NOT _hg_ovy45_get_work_original_found)
        message(FATAL_ERROR
            "OVY_45 native get-work wrapper: original member not found")
    endif()
endif()

foreach(id IN LISTS hg_selected_overlay_ids)
    set(target ${hg_overlay_${id}_target})
    if(TARGET ${target})
        set_property(TARGET ${target} PROPERTY SOURCES "${hg_overlay_${id}_sources}")
    else()
        add_library(${target} STATIC ${hg_overlay_${id}_sources})
        target_compile_definitions(${target} PRIVATE "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
        target_include_directories(${target} PRIVATE "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
        target_compile_options(${target} PRIVATE "$<$<COMPILE_LANGUAGE:C,CXX>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>")
        target_link_libraries(${target} PRIVATE nitro_config)
        add_dependencies(${target} heartgold_overlay_native_sources heartgold_native_headers fx_constants ${heartgold_asset_targets})
    endif()
    list(APPEND overlay_archives ${target})
    set(hg_overlay_${id}_archive ${target})
endforeach()

get_target_property(overlay_sdk_targets nitro_sdk INTERFACE_LINK_LIBRARIES)
set(overlay_main_targets heartgold_main heartgold_runtime heartgold_sound_storage native_host ${overlay_sdk_targets})
if(TARGET heartgold_guest32_account)
    list(APPEND overlay_main_targets heartgold_guest32_account heartgold_guest32_crc heartgold_guest32_std heartgold_guest32_runtime heartgold_guest32_mi)
endif()
set(overlay_link_args)
set(overlay_link_dependencies)
foreach(target IN LISTS overlay_main_targets)
    list(APPEND overlay_link_args --main "$<TARGET_FILE:${target}>")
    list(APPEND overlay_link_dependencies ${target} "$<TARGET_FILE:${target}>")
endforeach()
if(TARGET heartgold_guest32_account)
    foreach(name account crc std)
        set(manifest "${PROJECT_BINARY_DIR}/guest32-${name}/providers.json")
        list(APPEND overlay_link_args --provider-manifest "${manifest}")
        list(APPEND overlay_link_dependencies "${manifest}")
    endforeach()
    list(APPEND overlay_link_args --provider-manifest "${guest_mi_manifest}")
    list(APPEND overlay_link_dependencies "${guest_mi_manifest}" heartgold_guest32_mi_manifest)
endif()
foreach(id IN LISTS hg_selected_overlay_ids)
    set(target ${hg_overlay_${id}_archive})
    list(APPEND overlay_link_args --overlay "${id}=$<TARGET_FILE:${target}>")
    list(APPEND overlay_link_dependencies ${target} "$<TARGET_FILE:${target}>")
endforeach()
set(overlay_link_dir "${PROJECT_BINARY_DIR}/native-overlays")
set(overlay_imports "${overlay_link_dir}/imports.rsp")
set(overlay_exports "${overlay_link_dir}/main-exports.txt")
set(overlay_contracts "${overlay_link_dir}/providers.json")
set(overlay_registry "${overlay_link_dir}/provider-registry.json")
set(hg_interface_outputs "${overlay_link_dir}/interfaces/main.tbd")
foreach(id IN LISTS hg_selected_overlay_ids)
    list(APPEND hg_interface_outputs "${overlay_link_dir}/interfaces/image_${id}.tbd"
        "${overlay_link_dir}/image_${id}.rsp")
endforeach()
add_custom_command(OUTPUT ${hg_interface_outputs} "${overlay_imports}" "${overlay_exports}" "${overlay_contracts}" "${overlay_registry}"
    COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_LIST_DIR}/native_overlay_link.py"
        --nm "${CMAKE_NM}" --image-graph "${PROJECT_BINARY_DIR}/native-graph/images.json" ${overlay_link_args}
        --imports "${overlay_imports}" --exports "${overlay_exports}" --contracts "${overlay_contracts}"
    COMMAND "${CMAKE_COMMAND}" -E touch ${hg_interface_outputs}
        "${overlay_imports}" "${overlay_exports}" "${overlay_contracts}"
    DEPENDS ${overlay_link_dependencies} "${CMAKE_CURRENT_LIST_DIR}/native_overlay_link.py"
        "${CMAKE_CURRENT_LIST_DIR}/native_provider_registry.py" "${PROJECT_BINARY_DIR}/native-graph/images.json"
    VERBATIM)
add_custom_target(heartgold_overlay_link_contract DEPENDS ${hg_interface_outputs} "${overlay_imports}" "${overlay_exports}" "${overlay_contracts}" "${overlay_registry}")

# OVY_0 original-code partial provider: independently closed Wi-Fi exports.
# Do not duplicate these identities if full OVY_0 is selected.
if("0" IN_LIST hg_selected_overlay_ids)
    message(FATAL_ERROR
        "OVY_0 Wi-Fi subset conflicts with complete OVY_0 ownership")
endif()

set(hg_ovy0_wifi_source "${native_root}/src/wifi_connection.c")
add_library(hg_ovy0_wifi_subset SHARED "${hg_ovy0_wifi_source}")
target_compile_definitions(hg_ovy0_wifi_subset PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
target_include_directories(hg_ovy0_wifi_subset PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_options(hg_ovy0_wifi_subset PRIVATE
    "$<$<COMPILE_LANGUAGE:C,CXX>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>")
target_link_libraries(hg_ovy0_wifi_subset PRIVATE
    nitro_config "${overlay_link_dir}/interfaces/main.tbd")
target_link_options(hg_ovy0_wifi_subset PRIVATE
    "LINKER:-dead_strip"
    "LINKER:-exported_symbol,_WifiConnection_GetTargetFriendIndex"
    "LINKER:-exported_symbol,_WifiConnection_ClassifyErrorCode"
    "LINKER:-exported_symbol,_WifiConnection_SetDisconnectCallback")
set_target_properties(hg_ovy0_wifi_subset PROPERTIES
    OUTPUT_NAME "heartgold_ovy0_wifi_subset"
    LIBRARY_OUTPUT_DIRECTORY "${overlay_link_dir}"
    INSTALL_NAME_DIR "@rpath"
    BUILD_WITH_INSTALL_NAME_DIR TRUE)
add_dependencies(hg_ovy0_wifi_subset
    heartgold_overlay_native_sources
    heartgold_native_headers
    fx_constants
    heartgold_overlay_link_contract)

set(hg_native_image_targets)
set(hg_native_binding_args)
set(hg_native_binding_dependencies)
foreach(id IN LISTS hg_selected_overlay_ids)
    list(APPEND hg_native_image_targets heartgold_image_${id})
    set(archive ${hg_overlay_${id}_archive})
    set(anchor "${overlay_link_dir}/image_${id}.c")
    file(GENERATE OUTPUT "${anchor}" CONTENT "const unsigned HG_NativeOverlay${id}_ID = ${id};\n")
    add_library(heartgold_image_${id} SHARED "${anchor}")
    target_link_options(heartgold_image_${id} PRIVATE
        "LINKER:-force_load,$<TARGET_FILE:${archive}>" "@${overlay_link_dir}/image_${id}.rsp" "LINKER:-rpath,@loader_path")
    set_target_properties(heartgold_image_${id} PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${overlay_link_dir}"
        INSTALL_NAME_DIR "@rpath" BUILD_WITH_INSTALL_NAME_DIR TRUE
        LINK_DEPENDS "${hg_interface_outputs};$<TARGET_FILE:${archive}>")
    add_dependencies(heartgold_image_${id} heartgold_overlay_link_contract)

    if(id EQUAL 80)
        target_link_libraries(heartgold_image_80 PRIVATE
            hg_ovy0_wifi_subset)
    endif()
    add_custom_command(TARGET heartgold_image_${id} POST_BUILD
        COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_LIST_DIR}/native_overlay_preflight.py"
            --otool "${HG_NATIVE_OTOOL}" $<TARGET_FILE:heartgold_image_${id}>
        VERBATIM)
    target_link_libraries(heartgold PRIVATE heartgold_image_${id})
    list(APPEND hg_native_binding_args --image "${id}=$<TARGET_FILE:heartgold_image_${id}>")
    list(APPEND hg_native_binding_dependencies heartgold_image_${id} "$<TARGET_FILE:heartgold_image_${id}>")
endforeach()
add_custom_command(OUTPUT "${overlay_link_dir}/bindings.inc" "${overlay_link_dir}/bindings.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_LIST_DIR}/native_overlay_bindings.py"
        --contracts "${overlay_contracts}" ${hg_native_binding_args}
        --output "${overlay_link_dir}/bindings.inc" --report "${overlay_link_dir}/bindings.json"
    COMMAND "${CMAKE_COMMAND}" -E touch_nocreate "${overlay_link_dir}/bindings.inc"
    DEPENDS ${hg_native_binding_dependencies} "${overlay_contracts}"
        "${CMAKE_CURRENT_LIST_DIR}/native_overlay_bindings.py"
    VERBATIM)
add_custom_target(heartgold_overlay_bindings DEPENDS "${overlay_link_dir}/bindings.inc")
add_dependencies(heartgold heartgold_overlay_bindings)
set_property(TARGET heartgold APPEND PROPERTY LINK_DEPENDS "${overlay_exports}")
target_link_options(heartgold PRIVATE "LINKER:-export_dynamic" "LINKER:-exported_symbols_list,${overlay_exports}")
target_sources(heartgold PRIVATE "${PROJECT_SOURCE_DIR}/hardware_drivers/os/game_overlays.c")
target_compile_definitions(heartgold PRIVATE HG_NATIVE_OVERLAYS)
target_include_directories(heartgold PRIVATE "${overlay_link_dir}")
add_test(NAME native_overlay_manifest COMMAND "${Python3_EXECUTABLE}" -B -m unittest discover
    -s "${PROJECT_SOURCE_DIR}/tests" -p "test_native_overlay_manifest.py")

add_custom_target(heartgold_native_images DEPENDS ${hg_native_image_targets} heartgold_overlay_bindings)

add_test(NAME native_overlay_bindings COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_overlay_bindings.py"
    --build "${PROJECT_BINARY_DIR}" --sdk "${ntr_source}" --compiler "${CMAKE_C_COMPILER}")
add_test(NAME native_field_effect_abi COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_field_effect_abi.py" --build "${PROJECT_BINARY_DIR}")
add_test(NAME native_overlay_data COMMAND "${Python3_EXECUTABLE}" -B -m unittest discover
    -s "${PROJECT_SOURCE_DIR}/tests" -p "test_native_assembly*.py")

add_test(NAME native_dsprot_nsbta COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_dsprot_nsbta.py" --build "${PROJECT_BINARY_DIR}")
add_test(NAME native_nnsys_data COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_nnsys_native_data.py" --build "${PROJECT_BINARY_DIR}")

# OVY_39 private runtime views are checked against their actual source, not
# duplicated host declarations. Link only the real data member and SDK services.
add_custom_target(heartgold_global_terminal_data DEPENDS
    "${overlay_link_dir}/data/asm/global_terminal_data.S"
    "${overlay_link_dir}/data/asm/global_terminal_socket_data.S")
add_dependencies(heartgold_overlay_39 heartgold_global_terminal_data)
add_executable(test_global_terminal_layout "${PROJECT_SOURCE_DIR}/tests/test_global_terminal_layout.c"
    "${overlay_link_dir}/data/asm/global_terminal_socket_data.S")
add_dependencies(test_global_terminal_layout heartgold_global_terminal_data heartgold_overlay_native_sources heartgold_native_headers)
target_link_libraries(test_global_terminal_layout PRIVATE nitro_sdk)
target_include_directories(test_global_terminal_layout PRIVATE "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_definitions(test_global_terminal_layout PRIVATE "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>"
    HG_GLOBAL_TERMINAL_SOCKET_SOURCE="${native_root}/src/global_terminal/global_terminal_socket.c")
target_compile_options(test_global_terminal_layout PRIVATE
    "$<$<COMPILE_LANGUAGE:C>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>"
    "$<$<COMPILE_LANGUAGE:C>:-UNDEBUG;-fsanitize=address,undefined;-fno-sanitize-recover=all>")
target_link_options(test_global_terminal_layout PRIVATE -fsanitize=address,undefined -Wl,-dead_strip)
add_test(NAME global_terminal_native_layout COMMAND test_global_terminal_layout)
add_test(NAME global_terminal_native_data COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_global_terminal_native.py" --build "${PROJECT_BINARY_DIR}")
add_test(NAME global_terminal_native_images COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_global_terminal_native.py" --build "${PROJECT_BINARY_DIR}" --images)
set_tests_properties(global_terminal_native_images PROPERTIES TIMEOUT 120)

add_test(NAME global_terminal_native_image40 COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_global_terminal_native.py" --build "${PROJECT_BINARY_DIR}" --image 40)
set_tests_properties(global_terminal_native_layout PROPERTIES TIMEOUT 15)

add_custom_target(heartgold_image_report
    COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_LIST_DIR}/native_graph_report.py"
        --game "${game_source}" --build "${PROJECT_BINARY_DIR}"
        --out "${PROJECT_BINARY_DIR}/native-graph/report" --nm "${CMAKE_NM}"
    COMMENT "Inspect current native artifacts across the entire original image graph"
    VERBATIM)
add_test(NAME native_data_ir COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_data_ir.py")
add_test(NAME native_image_graph COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_image_graph.py")
set_tests_properties(native_data_ir native_image_graph PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")

add_test(NAME native_provider_registry COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_provider_registry.py")

add_test(NAME native_link_evidence COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_link_evidence.py")
add_test(NAME shared_provider_native COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_shared_provider_native.py")
set_tests_properties(shared_provider_native PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME native_abi COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_abi.py")
set_tests_properties(native_abi PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME dwc_backup_native COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_dwc_backup_native.py")
set_tests_properties(dwc_backup_native PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME spin_trade_native_data COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_spin_trade_data.py")
set_tests_properties(spin_trade_native_data PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME native_follow_data COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_follow_data.py")
set_tests_properties(native_overlay_manifest native_overlay_data native_link_evidence native_follow_data
    PROPERTIES ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")


# HEARTGOLD_OVY45_NATIVE_ITERATOR_ABI
# Scope the original pointer-sized iterator ABI to one native C member.
# Do not modify or relax the pinned Nintendo DS header.
if(TARGET heartgold_overlay_45)
    set_property(
        SOURCE "${game_source}/src/lobby/ppw_lobby_get_work.c"
        APPEND PROPERTY COMPILE_OPTIONS
        "-include"
        "${CMAKE_SOURCE_DIR}/native-adaptations/OVY_45/tree-iterator-native.h"
    )
endif()


# HEARTGOLD_OVY45_TARGET_ITERATOR_ABI
# OVY_45-wide native representation of the original DS iterator.
# Only C/C++ translation units receive this header; assembly does not.
# The pinned upstream sources and their DS assertions are unchanged.
if(TARGET heartgold_overlay_45)
    target_compile_options(heartgold_overlay_45 PRIVATE
        "$<$<OR:$<COMPILE_LANGUAGE:C>,$<COMPILE_LANGUAGE:CXX>>:SHELL:-include ${CMAKE_SOURCE_DIR}/native-adaptations/OVY_45/tree-iterator-native.h>"
    )
endif()
