# Source-owned storage regions; OVY_0 is never relabeled resident to link.
enable_language(ASM)
set(hg_dwc_data_dir "${PROJECT_BINARY_DIR}/dwc-native")
set(hg_dwc_data_driver "${CMAKE_CURRENT_LIST_DIR}/dwc_native_data.py")
set(hg_dwc_data_contract "${CMAKE_CURRENT_LIST_DIR}/dwc_native_inputs.json")
set(hg_dwc_bulk_manifest "${CMAKE_CURRENT_LIST_DIR}/dwc_ovy0_bulk_symbols.json")
set(hg_dwc_frontier_manifest "${CMAKE_CURRENT_LIST_DIR}/dwc_ovy0_frontier_symbols.json")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${hg_dwc_frontier_manifest}")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${hg_dwc_bulk_manifest}")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${hg_dwc_data_contract}")
file(READ "${hg_dwc_data_contract}" hg_dwc_data_inputs_json)
string(JSON hg_dwc_data_count LENGTH "${hg_dwc_data_inputs_json}")
math(EXPR hg_dwc_data_last "${hg_dwc_data_count}-1")
set(hg_dwc_data_inputs)
foreach(i RANGE 0 ${hg_dwc_data_last})
    string(JSON relative MEMBER "${hg_dwc_data_inputs_json}" ${i})
    list(APPEND hg_dwc_data_inputs "${game_source}/${relative}")
endforeach()
add_custom_command(OUTPUT "${hg_dwc_data_dir}/abi.c"
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_dwc_data_driver}"
        --game "${game_source}" --out "${hg_dwc_data_dir}"
    DEPENDS "${hg_dwc_data_driver}" "${hg_dwc_data_contract}" ${hg_dwc_data_inputs}
    VERBATIM)
add_library(heartgold_dwc_data_abi OBJECT "${hg_dwc_data_dir}/abi.c")
target_compile_definitions(heartgold_dwc_data_abi PRIVATE "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
target_include_directories(heartgold_dwc_data_abi PRIVATE "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_options(heartgold_dwc_data_abi PRIVATE "$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>")
target_link_libraries(heartgold_dwc_data_abi PRIVATE nitro_config)
add_dependencies(heartgold_dwc_data_abi heartgold_native_headers fx_constants)
add_custom_command(OUTPUT "${hg_dwc_data_dir}/main.S" "${hg_dwc_data_dir}/OVY_0.S"
        "${hg_dwc_data_dir}/OVY_0_qr.S" "${hg_dwc_data_dir}/OVY_0_bulk.S"
        "${hg_dwc_data_dir}/OVY_0_frontier.S"
        "${hg_dwc_data_dir}/manifest.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_dwc_data_driver}"
        --game "${game_source}" --out "${hg_dwc_data_dir}"
        --abi-object "$<TARGET_OBJECTS:heartgold_dwc_data_abi>"
    DEPENDS heartgold_dwc_data_abi $<TARGET_OBJECTS:heartgold_dwc_data_abi>
        "${hg_dwc_bulk_manifest}" "${hg_dwc_frontier_manifest}"
        "${hg_dwc_data_driver}" "${hg_dwc_data_contract}" ${hg_dwc_data_inputs}
        "${CMAKE_CURRENT_LIST_DIR}/native_storage.py" "${CMAKE_CURRENT_LIST_DIR}/native_data_ir.py"
        "${CMAKE_CURRENT_LIST_DIR}/native_assembly_data.py" "${CMAKE_CURRENT_LIST_DIR}/native_wifi_constants.py"
        "${game_source}/main.lsf"
    VERBATIM)
foreach(owner main OVY_0)
    add_library(heartgold_dwc_data_${owner} OBJECT "${hg_dwc_data_dir}/${owner}.S")
    add_custom_command(OUTPUT "${hg_dwc_data_dir}/${owner}-validated.json"
        COMMAND "${Python3_EXECUTABLE}" -B "${hg_dwc_data_driver}"
            --game "${game_source}" --out "${hg_dwc_data_dir}"
            --abi-object "$<TARGET_OBJECTS:heartgold_dwc_data_abi>"
            --validate "$<TARGET_OBJECTS:heartgold_dwc_data_${owner}>" --owner ${owner}
        DEPENDS heartgold_dwc_data_${owner} $<TARGET_OBJECTS:heartgold_dwc_data_${owner}>
            $<TARGET_OBJECTS:heartgold_dwc_data_abi> "${hg_dwc_data_dir}/manifest.json"
            "${hg_dwc_data_driver}" "${CMAKE_CURRENT_LIST_DIR}/native_storage.py"
            "${CMAKE_CURRENT_LIST_DIR}/native_assembly_data.py" "${CMAKE_CURRENT_LIST_DIR}/native_data_ir.py"
        VERBATIM)
    add_custom_target(heartgold_dwc_data_${owner}_verified DEPENDS "${hg_dwc_data_dir}/${owner}-validated.json")
endforeach()

# Exactly three original OVY_0 QR storage providers.
# The full OVY_0 storage object is deliberately NOT attached.
add_library(heartgold_dwc_data_OVY_0_qr OBJECT
    "${hg_dwc_data_dir}/OVY_0_qr.S")
set_property(TARGET heartgold_dwc_data_OVY_0_qr
    PROPERTY HG_ORIGINAL_OWNER OVY_0)

add_custom_command(
    OUTPUT "${hg_dwc_data_dir}/OVY_0_qr-validated.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_dwc_data_driver}"
        --game "${game_source}" --out "${hg_dwc_data_dir}"
        --abi-object "$<TARGET_OBJECTS:heartgold_dwc_data_abi>"
        --validate "$<TARGET_OBJECTS:heartgold_dwc_data_OVY_0_qr>"
        --owner OVY_0_qr
    DEPENDS heartgold_dwc_data_OVY_0_qr
        $<TARGET_OBJECTS:heartgold_dwc_data_OVY_0_qr>
        $<TARGET_OBJECTS:heartgold_dwc_data_abi>
        "${hg_dwc_data_dir}/manifest.json"
        "${hg_dwc_data_driver}"
        "${CMAKE_CURRENT_LIST_DIR}/native_storage.py"
        "${CMAKE_CURRENT_LIST_DIR}/native_assembly_data.py"
        "${CMAKE_CURRENT_LIST_DIR}/native_data_ir.py"
    VERBATIM)

add_custom_target(heartgold_dwc_data_OVY_0_qr_verified
    DEPENDS "${hg_dwc_data_dir}/OVY_0_qr-validated.json")

# hg_dwc_main is the existing native provider archive for OVY_0.
# Only the three QR records enter this archive.
target_sources(hg_dwc_main PRIVATE
    $<TARGET_OBJECTS:heartgold_dwc_data_OVY_0_qr>)
add_dependencies(hg_dwc_main heartgold_dwc_data_OVY_0_qr_verified)


# Source-owned OVY_0 data providers selected by a reviewed manifest.
# No complete OVY_0 object, duplicate QR storage, or owner reassignment.
add_library(heartgold_dwc_data_OVY_0_bulk OBJECT
    "${hg_dwc_data_dir}/OVY_0_bulk.S")
set_property(TARGET heartgold_dwc_data_OVY_0_bulk
    PROPERTY HG_ORIGINAL_OWNER OVY_0)

add_custom_command(
    OUTPUT "${hg_dwc_data_dir}/OVY_0_bulk-validated.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_dwc_data_driver}"
        --game "${game_source}" --out "${hg_dwc_data_dir}"
        --abi-object "$<TARGET_OBJECTS:heartgold_dwc_data_abi>"
        --validate "$<TARGET_OBJECTS:heartgold_dwc_data_OVY_0_bulk>"
        --owner OVY_0_bulk
    DEPENDS heartgold_dwc_data_OVY_0_bulk
        $<TARGET_OBJECTS:heartgold_dwc_data_OVY_0_bulk>
        $<TARGET_OBJECTS:heartgold_dwc_data_abi>
        "${hg_dwc_data_dir}/manifest.json"
        "${hg_dwc_bulk_manifest}"
        "${hg_dwc_data_driver}"
        "${CMAKE_CURRENT_LIST_DIR}/native_storage.py"
        "${CMAKE_CURRENT_LIST_DIR}/native_assembly_data.py"
        "${CMAKE_CURRENT_LIST_DIR}/native_data_ir.py"
    VERBATIM)

add_custom_target(heartgold_dwc_data_OVY_0_bulk_verified
    DEPENDS "${hg_dwc_data_dir}/OVY_0_bulk-validated.json")

target_sources(hg_dwc_main PRIVATE
    $<TARGET_OBJECTS:heartgold_dwc_data_OVY_0_bulk>)
add_dependencies(hg_dwc_main
    heartgold_dwc_data_OVY_0_bulk_verified)


# Independent, source-owned OVY_0 frontier storage.
add_library(heartgold_dwc_data_OVY_0_frontier OBJECT
    "${hg_dwc_data_dir}/OVY_0_frontier.S")
set_property(TARGET heartgold_dwc_data_OVY_0_frontier
    PROPERTY HG_ORIGINAL_OWNER OVY_0)

add_custom_command(
    OUTPUT "${hg_dwc_data_dir}/OVY_0_frontier-validated.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_dwc_data_driver}"
        --game "${game_source}" --out "${hg_dwc_data_dir}"
        --abi-object "$<TARGET_OBJECTS:heartgold_dwc_data_abi>"
        --validate "$<TARGET_OBJECTS:heartgold_dwc_data_OVY_0_frontier>"
        --owner OVY_0_frontier
    DEPENDS heartgold_dwc_data_OVY_0_frontier
        $<TARGET_OBJECTS:heartgold_dwc_data_OVY_0_frontier>
        $<TARGET_OBJECTS:heartgold_dwc_data_abi>
        "${hg_dwc_data_dir}/manifest.json"
        "${hg_dwc_frontier_manifest}"
        "${hg_dwc_data_driver}"
        "${CMAKE_CURRENT_LIST_DIR}/native_storage.py"
        "${CMAKE_CURRENT_LIST_DIR}/native_assembly_data.py"
        "${CMAKE_CURRENT_LIST_DIR}/native_data_ir.py"
    VERBATIM)

add_custom_target(heartgold_dwc_data_OVY_0_frontier_verified
    DEPENDS "${hg_dwc_data_dir}/OVY_0_frontier-validated.json")

target_sources(hg_dwc_main PRIVATE
    $<TARGET_OBJECTS:heartgold_dwc_data_OVY_0_frontier>)
add_dependencies(hg_dwc_main
    heartgold_dwc_data_OVY_0_frontier_verified)

# BEGIN REVIEWED OVY_0 MATCH KEY STORAGE
# Original OVY_0 BSS aggregate, widened under explicit native ABI assertions.
# Keep outside hg_dwc_main's original-C semantic-slot census.
add_library(heartgold_dwc_data_OVY_0_match_keys OBJECT
    "${PROJECT_SOURCE_DIR}/cmake/dwc_match_keys_native.c")
set_property(TARGET heartgold_dwc_data_OVY_0_match_keys
    PROPERTY HG_ORIGINAL_OWNER OVY_0)
target_include_directories(heartgold_dwc_data_OVY_0_match_keys PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_definitions(heartgold_dwc_data_OVY_0_match_keys PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
target_compile_options(heartgold_dwc_data_OVY_0_match_keys PRIVATE
    "$<$<COMPILE_LANGUAGE:C>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>")
target_link_libraries(heartgold_dwc_data_OVY_0_match_keys PRIVATE nitro_config)
add_dependencies(heartgold_dwc_data_OVY_0_match_keys
    heartgold_native_headers fx_constants)

target_sources(hg_dwc_main PRIVATE
    $<TARGET_OBJECTS:heartgold_dwc_data_OVY_0_match_keys>)
add_dependencies(hg_dwc_main
    heartgold_dwc_data_OVY_0_match_keys)
# END REVIEWED OVY_0 MATCH KEY STORAGE

target_sources(heartgold_main PRIVATE $<TARGET_OBJECTS:heartgold_dwc_data_main>)
add_dependencies(heartgold_main heartgold_dwc_data_main_verified)
# The current OVY_0 image is incomplete. In addition, the original AC socket
# template is copied with an ARM32 byte count across an untyped adjacent record.
# These are execution admission blockers, not conditions a data-only object
# validator can waive. Do not attach this object merely if an image target later
# appears: the remaining consumer ABI and duplicate-provider checks must pass.
set_property(TARGET heartgold_dwc_data_OVY_0 PROPERTY HG_ORIGINAL_OWNER OVY_0)
set_property(TARGET heartgold_dwc_data_main PROPERTY HG_ORIGINAL_OWNER main)
add_custom_target(heartgold_dwc_native_data DEPENDS
    heartgold_dwc_data_main_verified heartgold_dwc_data_OVY_0_verified
    heartgold_dwc_data_OVY_0_qr_verified
    heartgold_dwc_data_OVY_0_bulk_verified
    heartgold_dwc_data_OVY_0_frontier_verified)
add_test(NAME dwc_typed_data COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_dwc_typed_data.py" --build "${PROJECT_BINARY_DIR}"
    --game "${game_source}" --compiler "${CMAKE_C_COMPILER}")
add_test(NAME dwc_typed_data_build COMMAND "${CMAKE_COMMAND}" --build
    "${PROJECT_BINARY_DIR}" --target heartgold_dwc_native_data heartgold_main
    hg_dwc_main hg_dwc_status_code -j8)
set_tests_properties(dwc_typed_data_build PROPERTIES FIXTURES_SETUP dwc_typed_data_ready RUN_SERIAL TRUE)
set_tests_properties(dwc_typed_data PROPERTIES FIXTURES_REQUIRED dwc_typed_data_ready RUN_SERIAL TRUE)
