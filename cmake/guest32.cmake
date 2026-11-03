# Original-image compiler admission. Partial function objects never become image
# providers: the complete-member target must succeed before representation review.
set(LLVM_DIR "${HEARTGOLD_GUEST32_LLVM_DIR}")
set(GUEST32_GAME_BINARY_DIR "${PROJECT_BINARY_DIR}")
add_subdirectory("${PROJECT_SOURCE_DIR}/compiler/guest32" "${PROJECT_BINARY_DIR}/guest32-compiler")
get_target_property(guest32_tools guest32-lower HG_LLVM_TOOLS_DIR)
set(guest32_dir "${PROJECT_BINARY_DIR}/guest32-ovy0")
set(guest32_original "${game_source}/lib/NitroDWC/src/match_browse.c")
set(guest32_ir "${guest32_dir}/match_browse.ll")
set(guest32_native_ir "${guest32_dir}/native.ll")
set(guest32_abi "${PROJECT_SOURCE_DIR}/compiler/guest32/dwc_abi.json")
add_custom_command(OUTPUT "${guest32_ir}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${guest32_dir}"
    COMMAND "${guest32_tools}/clang" -target armv5-apple-darwin
        -ffreestanding -fno-builtin -fsigned-char -fno-short-enums -std=gnu89
        -DSDK_ARM9 -DSDK_CODE_ARM -DSDK_FINALROM
        "-I${PROJECT_BINARY_DIR}/include" "-I${game_source}/include"
        "-I${game_source}/include/library" "-I${game_source}/lib/include"
        "-I${game_source}/lib/NitroSDK/include"
        -O0 -Xclang -disable-O0-optnone -Xclang -disable-llvm-passes
        -MD -MF "${guest32_ir}.d" -MT "${guest32_ir}"
        -S -emit-llvm "${guest32_original}" -o "${guest32_ir}"
    DEPENDS "${guest32_original}" fx_constants
    DEPFILE "${guest32_ir}.d" VERBATIM)
add_custom_command(OUTPUT "${guest32_native_ir}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${guest32_dir}"
    COMMAND "${guest32_tools}/clang" -O0 -S -emit-llvm
        "${PROJECT_SOURCE_DIR}/hardware_drivers/guest32_dwc.c" -o "${guest32_native_ir}"
        -MD -MF "${guest32_native_ir}.d" -MT "${guest32_native_ir}"
    DEPENDS "${PROJECT_SOURCE_DIR}/hardware_drivers/guest32_dwc.c"
    DEPFILE "${guest32_native_ir}.d" VERBATIM)
add_custom_target(heartgold_guest32_ovy0_ir DEPENDS "${guest32_ir}" "${guest32_native_ir}")
add_custom_command(OUTPUT "${guest32_dir}/match_browse.native.ll"
    COMMAND $<TARGET_FILE:guest32-lower> "${guest32_ir}" "${guest32_dir}/match_browse.native.ll"
        --abi "${guest32_abi}" --native-ir "${guest32_native_ir}" --prefix guest32_
    DEPENDS guest32-lower "${guest32_ir}" "${guest32_native_ir}" "${guest32_abi}" VERBATIM)
add_custom_command(OUTPUT "${guest32_dir}/match_browse.o"
    COMMAND "${CMAKE_C_COMPILER}" -O2 -c "${guest32_dir}/match_browse.native.ll"
        -o "${guest32_dir}/match_browse.o"
    DEPENDS "${guest32_dir}/match_browse.native.ll" VERBATIM)
# Whole-image admission is manifest complete. Never expose a partial archive.
file(READ "${PROJECT_BINARY_DIR}/native-graph/images.json" guest32_model)
string(JSON guest32_count LENGTH "${guest32_model}" images OVY_0 objects)
math(EXPR guest32_last "${guest32_count}-1")
set(guest32_image_inputs)
foreach(i RANGE 0 ${guest32_last})
    string(JSON obj GET "${guest32_model}" images OVY_0 objects ${i})
    string(JSON relative GET "${guest32_model}" members "${obj}" source)
    list(APPEND guest32_image_inputs "${game_source}/${relative}")
endforeach()
file(GLOB_RECURSE guest32_headers CONFIGURE_DEPENDS
    "${game_source}/include/*.h" "${game_source}/lib/include/*.h")
set(guest32_image_dir "${PROJECT_BINARY_DIR}/guest32-ovy0-image")
set(guest32_driver "${PROJECT_SOURCE_DIR}/compiler/guest32/image.py")
add_custom_command(OUTPUT "${guest32_image_dir}/complete.stamp"
    COMMAND "${Python3_EXECUTABLE}" -B "${guest32_driver}" --game "${game_source}"
        --build "${PROJECT_BINARY_DIR}" --out "${guest32_image_dir}"
        --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>
    DEPENDS guest32-lower fx_constants "${game_source}/main.lsf" ${guest32_image_inputs} ${guest32_headers}
        "${guest32_driver}" "${PROJECT_SOURCE_DIR}/compiler/guest32/incremental.py"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/original_layout.py"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/original_data_layouts.json"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/ovy0_registers.json"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/ovy0_layout.json"
        "${game_source}/lib/NitroDWC/src/available_check_poll.alias-map.json"
    DEPFILE "${guest32_image_dir}/image.d"
    VERBATIM)
add_custom_target(heartgold_guest32_ovy0 DEPENDS "${guest32_image_dir}/complete.stamp")

set(guest32_archive "${guest32_image_dir}/libheartgold_overlay_0.a")
add_custom_command(
    OUTPUT "${guest32_archive}"
    COMMAND "${Python3_EXECUTABLE}" -B
        "${PROJECT_SOURCE_DIR}/compiler/guest32/archive.py"
        --coverage "${guest32_image_dir}/coverage.json"
        --image-dir "${guest32_image_dir}"
        --archive "${guest32_archive}"
        --ar "${guest32_tools}/llvm-ar"
        --image-name OVY_0
    DEPENDS
        "${guest32_image_dir}/complete.stamp"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/archive.py"
    VERBATIM
)
add_custom_target(
    heartgold_guest32_ovy0_archive
    DEPENDS "${guest32_archive}"
)

add_custom_target(heartgold_guest32_ovy0_coverage
    COMMAND "${Python3_EXECUTABLE}" -B "${guest32_driver}" --game "${game_source}"
        --build "${PROJECT_BINARY_DIR}" --out "${guest32_image_dir}"
        --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower> --report-only
    DEPENDS guest32-lower fx_constants VERBATIM)
add_custom_command(OUTPUT "${guest32_dir}/match_keys.functions.ll"
    COMMAND $<TARGET_FILE:guest32-lower> "${guest32_ir}" "${guest32_dir}/match_keys.functions.ll"
        --abi "${guest32_abi}" --native-ir "${guest32_native_ir}" --prefix guest32_
        --entry DWCi_GetNewMatchKeyID --entry DWCi_ClearMatchKeys
    DEPENDS guest32-lower "${guest32_ir}" "${guest32_native_ir}" "${guest32_abi}" VERBATIM)
add_custom_target(heartgold_guest32_match_keys ALL DEPENDS "${guest32_dir}/match_keys.functions.ll")
add_dependencies(heartgold_guest32_match_keys heartgold_overlay_native_sources)
add_test(NAME guest32_ovy0_pipeline COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_bridge.py" --build "${PROJECT_BINARY_DIR}/guest32-ovy0-tests"
    --game-build "${PROJECT_BINARY_DIR}" --llvm-config "${guest32_tools}/llvm-config"
    --lowerer $<TARGET_FILE:guest32-lower> --original-ir "${guest32_ir}")

# Host-side support for guest-addressed native ARM64 execution.
# Separate from original-image membership.
add_library(heartgold_guest32_runtime STATIC
    "${PROJECT_SOURCE_DIR}/hardware_drivers/guest32.c")
set_target_properties(heartgold_guest32_runtime PROPERTIES
    C_STANDARD 11
    C_STANDARD_REQUIRED YES)

# Rebuild original CPS/VCT providers with validated ARM assembly lowering.
# These archives are not automatically admitted across the guest32 ABI.
add_custom_target(heartgold_guest32_sdk_providers
    COMMAND "${Python3_EXECUTABLE}" -B
        "${PROJECT_SOURCE_DIR}/compiler/guest32/build_sdk_providers.py"
        --build "${PROJECT_BINARY_DIR}" --llvm-bin "${guest32_tools}"
    BYPRODUCTS
        "${PROJECT_BINARY_DIR}/guest32-sdk-providers/providers.json"
        "${PROJECT_BINARY_DIR}/guest32-sdk-providers/libheartgold_libCPS_complete.a"
        "${PROJECT_BINARY_DIR}/guest32-sdk-providers/libheartgold_libVCT_complete.a"
    DEPENDS fx_constants heartgold_native_headers
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    VERBATIM
)
add_test(NAME guest32_incremental COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_incremental.py")
set_tests_properties(guest32_incremental PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME guest32_image_execution COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_image.py"
    --build "${PROJECT_BINARY_DIR}" --image-dir "${guest32_image_dir}"
    --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>)
add_test(NAME guest32_ds_execution COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_ds.py"
    --build "${PROJECT_BINARY_DIR}" --llvm-bin "${guest32_tools}"
    --lowerer $<TARGET_FILE:guest32-lower>)

# Complete original main-image provider members, retaining the guest ABI.
function(heartgold_guest_provider name member)
    set(dir "${PROJECT_BINARY_DIR}/guest32-${name}")
    string(REGEX REPLACE "\\.o$" ".c" source "${member}")
    add_custom_command(OUTPUT "${dir}/provider.a" "${dir}/providers.json"
        BYPRODUCTS "${dir}/provider.o" "${dir}/guest.ll" "${dir}/native.ll"
            "${dir}/abi.json" "${dir}/native-abi.ll" "${dir}/description.json" "${dir}/headers.json"
            "${dir}/guest.ll.d" "${dir}/guest.ll.receipt.json" "${dir}/native.ll.receipt.json"
            "${dir}/provider.o.receipt.json" "${dir}/provider.d"
        COMMAND "${Python3_EXECUTABLE}" -B "${PROJECT_SOURCE_DIR}/compiler/guest32/member.py"
            --game "${game_source}" --build "${PROJECT_BINARY_DIR}" --out "${dir}"
            --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>
            --owner main --member "${member}"
        DEPENDS guest32-lower fx_constants "${game_source}/${source}" "${game_source}/main.lsf"
            "${PROJECT_SOURCE_DIR}/compiler/guest32/member.py"
            "${PROJECT_SOURCE_DIR}/compiler/guest32/incremental.py"
        DEPFILE "${dir}/provider.d" VERBATIM)
    add_custom_target(heartgold_guest32_${name}_build DEPENDS "${dir}/provider.a" "${dir}/providers.json")
    add_library(heartgold_guest32_${name} STATIC IMPORTED GLOBAL)
    set_target_properties(heartgold_guest32_${name} PROPERTIES IMPORTED_LOCATION "${dir}/provider.a")
    add_dependencies(heartgold_guest32_${name} heartgold_guest32_${name}_build)
    target_link_libraries(heartgold PRIVATE heartgold_guest32_${name})
endfunction()
heartgold_guest_provider(account lib/NitroDWC/src/dwc_account.o)
heartgold_guest_provider(crc lib/NitroSDK/src/math/MATH_crc.o)
heartgold_guest_provider(std lib/NitroSDK/src/std_string.o)
target_link_libraries(heartgold PRIVATE heartgold_guest32_runtime)

set(guest38_dir "${PROJECT_BINARY_DIR}/guest32-ovy38-image")
set(guest38_inputs)
string(JSON guest38_count LENGTH "${guest32_model}" images OVY_38 objects)
math(EXPR guest38_last "${guest38_count}-1")
foreach(i RANGE 0 ${guest38_last})
    string(JSON obj GET "${guest32_model}" images OVY_38 objects ${i})
    string(JSON relative GET "${guest32_model}" members "${obj}" source)
    list(APPEND guest38_inputs "${game_source}/${relative}")
endforeach()
add_custom_command(OUTPUT "${guest38_dir}/complete.stamp"
    COMMAND "${Python3_EXECUTABLE}" -B "${guest32_driver}" --image OVY_38 --game "${game_source}"
        --build "${PROJECT_BINARY_DIR}" --out "${guest38_dir}"
        --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>
    DEPENDS guest32-lower fx_constants "${game_source}/main.lsf" ${guest38_inputs}
        "${guest32_driver}" "${PROJECT_SOURCE_DIR}/compiler/guest32/incremental.py"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/original_layout.py"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/original_data_layouts.json"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/ovy38_registers.json"
    DEPFILE "${guest38_dir}/image.d" VERBATIM)
add_custom_command(OUTPUT "${guest38_dir}/libheartgold_overlay_38.a"
    COMMAND "${Python3_EXECUTABLE}" -B "${PROJECT_SOURCE_DIR}/compiler/guest32/archive.py"
        --coverage "${guest38_dir}/coverage.json" --image-dir "${guest38_dir}"
        --archive "${guest38_dir}/libheartgold_overlay_38.a" --ar "${guest32_tools}/llvm-ar" --image-name OVY_38
    DEPENDS "${guest38_dir}/complete.stamp" "${PROJECT_SOURCE_DIR}/compiler/guest32/archive.py" VERBATIM)
add_custom_target(heartgold_guest32_ovy38_archive DEPENDS "${guest38_dir}/libheartgold_overlay_38.a")

add_library(heartgold_guest32_scalar_bridges STATIC
    "${PROJECT_SOURCE_DIR}/compiler/guest32/cps_scalar_bridge.c"
    "${PROJECT_SOURCE_DIR}/compiler/guest32/cps_scalar_args_bridge.c"
    "${PROJECT_SOURCE_DIR}/compiler/guest32/vct_scalar_bridge.c")
target_compile_options(heartgold_guest32_scalar_bridges PRIVATE "-idirafter${game_source}/lib/include")
target_include_directories(heartgold_guest32_scalar_bridges PRIVATE "${native_root}/lib/include")
add_dependencies(heartgold_guest32_scalar_bridges heartgold_native_headers)
target_link_libraries(heartgold_guest32_scalar_bridges PRIVATE nitro_sdk)
add_library(heartgold_guest32_libc_memory STATIC "${PROJECT_SOURCE_DIR}/compiler/guest32/libc_memory_bridge.c")
target_include_directories(heartgold_guest32_libc_memory PRIVATE "${PROJECT_SOURCE_DIR}")
add_test(NAME guest32_closure_execution COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_closure.py" --build "${PROJECT_BINARY_DIR}"
    --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>)
add_custom_target(heartgold_guest32_link_diagnostics
    COMMAND "${Python3_EXECUTABLE}" -B "${PROJECT_SOURCE_DIR}/cmake/guest32_closure.py"
        --build "${PROJECT_BINARY_DIR}" --compiler "${CMAKE_C_COMPILER}"
    DEPENDS heartgold_guest32_ovy0_archive heartgold_guest32_ovy38_archive
        heartgold_guest32_account_build heartgold_guest32_crc_build heartgold_guest32_runtime
        heartgold_guest32_std_build
        heartgold_guest32_scalar_bridges heartgold_guest32_libc_memory heartgold_overlay_link_contract
    VERBATIM)

# Original MI memory instructions in the existing shared guest representation.
# Keep the SDK_PORT byte-pattern clear and memcpy implementation out of this path.
set(guest_mi_source "${PROJECT_BINARY_DIR}/guest32-mi/mi_memory.c")
native_generate(guest-mi-memory "${game_source}/lib/NitroSDK/src/mi/mi_memory.c"
    "${guest_mi_source}" "${PROJECT_SOURCE_DIR}/cmake/native_mi.py")
add_library(heartgold_guest32_mi STATIC "${guest_mi_source}")
target_include_directories(heartgold_guest32_mi PRIVATE "${PROJECT_SOURCE_DIR}/hardware_drivers")
set(guest_mi_manifest "${PROJECT_BINARY_DIR}/guest32-mi/providers.json")
add_custom_command(OUTPUT "${guest_mi_manifest}"
    COMMAND "${Python3_EXECUTABLE}" -B "${PROJECT_SOURCE_DIR}/cmake/native_mi.py"
        --source "${game_source}/lib/NitroSDK/src/mi/mi_memory.c"
        --archive $<TARGET_FILE:heartgold_guest32_mi> --out "${guest_mi_manifest}" --nm "${CMAKE_NM}"
    DEPENDS heartgold_guest32_mi "${PROJECT_SOURCE_DIR}/cmake/native_mi.py"
        "${game_source}/lib/NitroSDK/src/mi/mi_memory.c" VERBATIM)
add_custom_target(heartgold_guest32_mi_manifest DEPENDS "${guest_mi_manifest}")
target_link_libraries(heartgold PRIVATE heartgold_guest32_mi)
add_dependencies(heartgold_guest32_link_diagnostics heartgold_guest32_mi_manifest)
add_test(NAME guest32_mi_execution COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_mi.py" --build "${PROJECT_BINARY_DIR}"
    --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>)
add_test(NAME guest32_std_execution COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_std.py" --build "${PROJECT_BINARY_DIR}"
    --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>)
