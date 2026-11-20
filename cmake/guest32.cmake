# Original-image compiler admission. Partial function objects never become image
# providers: the complete-member target must succeed before representation review.
set(LLVM_DIR "${HEARTGOLD_GUEST32_LLVM_DIR}")
set(GUEST32_GAME_BINARY_DIR "${PROJECT_BINARY_DIR}")
add_subdirectory("${PROJECT_SOURCE_DIR}/compiler/guest32" "${PROJECT_BINARY_DIR}/guest32-compiler")
get_target_property(guest32_tools guest32-lower HG_LLVM_TOOLS_DIR)
include("${CMAKE_CURRENT_LIST_DIR}/wm_guest32.cmake")
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
set(guest32_image_inputs ${hg_original_image_OVY_0_inputs})
file(GLOB_RECURSE guest32_headers CONFIGURE_DEPENDS
    "${game_source}/include/*.h" "${game_source}/lib/include/*.h")
set(guest32_image_dir "${PROJECT_BINARY_DIR}/guest32-ovy0-image")
set(guest32_driver "${PROJECT_SOURCE_DIR}/compiler/guest32/image.py")
set(guest32_frontend_inputs
    "${PROJECT_SOURCE_DIR}/compiler/guest32/frontend.py"
    "${PROJECT_SOURCE_DIR}/compiler/guest32/frontend_cache.py"
    "${PROJECT_SOURCE_DIR}/cmake/native_sources.py"
    "${PROJECT_SOURCE_DIR}/cmake/native_pristine_compat.json")
add_custom_command(OUTPUT "${guest32_image_dir}/complete.stamp"
    BYPRODUCTS "${guest32_image_dir}/frontend-coverage.json" "${guest32_image_dir}/inline-identities.json" "${guest32_image_dir}/ownership-conflicts.json"
        "${guest32_image_dir}/compiler-catalog.json" "${guest32_image_dir}/compile-profile.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${guest32_driver}" --game "${game_source}"
        --build "${PROJECT_BINARY_DIR}" --out "${guest32_image_dir}"
        --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>
    DEPENDS guest32-lower fx_constants "${game_source}/main.lsf" ${guest32_image_inputs} ${guest32_headers}
        "${guest32_driver}" ${guest32_frontend_inputs} "${PROJECT_SOURCE_DIR}/compiler/guest32/incremental.py"
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
    "${PROJECT_SOURCE_DIR}/hardware_drivers/guest32.c"
    "${PROJECT_SOURCE_DIR}/hardware_drivers/guest32_overlay.c")
enable_language(ASM)
add_library(heartgold_guest32_context STATIC
    "${PROJECT_SOURCE_DIR}/hardware_drivers/guest32_context.c"
    "${PROJECT_SOURCE_DIR}/hardware_drivers/guest32_context.S")
add_library(heartgold_guest32_cache STATIC
    "${PROJECT_SOURCE_DIR}/hardware_drivers/guest32_cache.c")
target_link_libraries(heartgold_guest32_cache PUBLIC ntr_os)
set_target_properties(heartgold_guest32_runtime PROPERTIES
    C_STANDARD 11
    C_STANDARD_REQUIRED YES)

heartgold_test_fixture(guest32_callbacks guest32-lower test_os heartgold_guest32_runtime)
add_test(NAME guest32_original_callbacks COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_callbacks.py" --build "${PROJECT_BINARY_DIR}"
    --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>)
set_tests_properties(guest32_original_callbacks PROPERTIES FIXTURES_REQUIRED guest32_callbacks)
add_test(NAME guest32_whole_program_projection COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_whole_program.py")
add_test(NAME guest32_call_results COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_call_results.py" --build "${PROJECT_BINARY_DIR}"
    --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>)
add_custom_target(heartgold_whole_program_plan
    COMMAND "${Python3_EXECUTABLE}" -B "${PROJECT_SOURCE_DIR}/compiler/guest32/whole_program.py"
        --game "${game_source}" --build "${PROJECT_BINARY_DIR}"
        --out "${PROJECT_BINARY_DIR}/whole-program/plan.json"
    BYPRODUCTS "${PROJECT_BINARY_DIR}/whole-program/plan.json"
    DEPENDS heartgold_guest32_provider_closure
        "${PROJECT_SOURCE_DIR}/compiler/guest32/whole_program.py"
    VERBATIM)

add_test(NAME guest32_incremental COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_incremental.py")
set_tests_properties(guest32_incremental PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME guest32_provider_catalog COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_extra_roots.py"
    --build "${PROJECT_BINARY_DIR}" --lowerer $<TARGET_FILE:guest32-lower>)
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
            "${PROJECT_SOURCE_DIR}/compiler/guest32/original_layout.py"
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
set(guest38_inputs ${hg_original_image_OVY_38_inputs})
add_custom_command(OUTPUT "${guest38_dir}/complete.stamp"
    BYPRODUCTS "${guest38_dir}/frontend-coverage.json" "${guest38_dir}/inline-identities.json" "${guest38_dir}/ownership-conflicts.json"
        "${guest38_dir}/compiler-catalog.json" "${guest38_dir}/compile-profile.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${guest32_driver}" --image OVY_38 --game "${game_source}"
        --build "${PROJECT_BINARY_DIR}" --out "${guest38_dir}"
        --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>
    DEPENDS guest32-lower fx_constants "${game_source}/main.lsf" ${guest38_inputs}
        "${guest32_driver}" ${guest32_frontend_inputs} "${PROJECT_SOURCE_DIR}/compiler/guest32/incremental.py"
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
        --build "${PROJECT_BINARY_DIR}" --compiler "${CMAKE_C_COMPILER}" --lowerer $<TARGET_FILE:guest32-lower>
        --diagnostic-stages
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

# Joint placement is separate from native image admission. Original overlay
# archives and explicit initializers retain their original ownership/lifetimes.
set(guest32_shared_dir "${PROJECT_BINARY_DIR}/guest32-shared")
set(guest32_shared_outputs "${guest32_shared_dir}/shared.json" "${guest32_shared_dir}/shared.d")
foreach(id IN ITEMS 0 38)
    set(dir "${guest32_shared_dir}/OVY_${id}")
    list(APPEND guest32_shared_outputs "${dir}/libheartgold_overlay_${id}.a"
        "${dir}/plan.json" "${dir}/image.json" "${dir}/coverage.json" "${dir}/frontend-coverage.json" "${dir}/inline-identities.json" "${dir}/ownership-conflicts.json" "${dir}/data-relocations.json"
        "${dir}/cross-unit-abi.json" "${dir}/complete.stamp" "${dir}/image.d" "${dir}/native-abi.ll")
    list(APPEND guest32_shared_outputs "${dir}/compiler-catalog.json" "${dir}/compile-profile.json")
    set(objects ${hg_original_image_OVY_${id}_objects})
    set(inputs ${hg_original_image_OVY_${id}_inputs})
    list(LENGTH objects count)
    math(EXPR last "${count}-1")
    foreach(i RANGE 0 ${last})
        list(GET objects ${i} obj)
        list(APPEND guest32_shared_outputs "${dir}/${obj}/native.o")
        if(obj IN_LIST hg_original_image_OVY_${id}_C_objects)
            foreach(file IN ITEMS guest.bc guest.bc.receipt.json guest.ll guest.ll.d frontend.log operations.json
                    abi.json compiler-catalog.json native.ll native.ll.receipt.json lower.log native.o.receipt.json object.log)
                list(APPEND guest32_shared_outputs "${dir}/${obj}/${file}")
            endforeach()
        else()
            foreach(file IN ITEMS data.c data.d native.o.receipt.json object.log)
                list(APPEND guest32_shared_outputs "${dir}/${obj}/${file}")
            endforeach()
            # Section .bin dumps are diagnostics, not inputs to the emitted C
            # or archive. Empty declared sections intentionally emit no dump.
        endif()
    endforeach()
endforeach()
add_custom_command(OUTPUT "${guest32_shared_dir}/complete.stamp"
    BYPRODUCTS ${guest32_shared_outputs}
    COMMAND "${Python3_EXECUTABLE}" -B "${PROJECT_SOURCE_DIR}/compiler/guest32/shared.py"
        --game "${game_source}" --build "${PROJECT_BINARY_DIR}" --out "${guest32_shared_dir}"
        --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>
    DEPENDS guest32-lower fx_constants heartgold_native_headers ${guest32_image_inputs} ${guest38_inputs} ${guest32_headers}
        "${game_source}/main.lsf" "${guest32_driver}" ${guest32_frontend_inputs}
        "${PROJECT_SOURCE_DIR}/compiler/guest32/shared.py"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/archive.py"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/incremental.py"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/original_layout.py"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/original_data_layouts.json"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/ovy0_layout.json"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/ovy0_registers.json"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/ovy38_registers.json"
        "${PROJECT_SOURCE_DIR}/cmake/native_data_layouts.py"
        "${PROJECT_SOURCE_DIR}/cmake/native_data_layouts.json"
    DEPFILE "${guest32_shared_dir}/shared.d"
    VERBATIM)
add_custom_target(heartgold_guest32_shared DEPENDS "${guest32_shared_dir}/complete.stamp")
add_custom_target(heartgold_guest32_shared_link_diagnostics
    COMMAND "${Python3_EXECUTABLE}" -B "${PROJECT_SOURCE_DIR}/cmake/guest32_closure.py"
        --build "${PROJECT_BINARY_DIR}" --compiler "${CMAKE_C_COMPILER}" --lowerer $<TARGET_FILE:guest32-lower>
        --diagnostic-stages
        --image-root "${guest32_shared_dir}" --out "${guest32_shared_dir}/links"
    DEPENDS heartgold_guest32_shared heartgold_guest32_account_build heartgold_guest32_crc_build
        heartgold_guest32_std_build heartgold_guest32_runtime heartgold_guest32_mi_manifest
        heartgold_guest32_scalar_bridges heartgold_guest32_libc_memory heartgold_overlay_link_contract
    VERBATIM)
heartgold_test_fixture(guest32_shared heartgold_guest32_shared heartgold_guest32_ovy38_archive
        heartgold_guest32_account_build heartgold_guest32_crc_build
        heartgold_guest32_std_build heartgold_guest32_mi_manifest)
add_test(NAME guest32_shared_execution COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_shared.py" --build "${PROJECT_BINARY_DIR}"
    --image-root "${guest32_shared_dir}" --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>)
set_tests_properties(guest32_shared_execution PROPERTIES FIXTURES_REQUIRED guest32_shared)
set_tests_properties(guest32_closure_execution guest32_mi_execution guest32_std_execution
    PROPERTIES FIXTURES_REQUIRED guest32_shared)

# Deliberately bounded software experiments, not admission of complete images.
add_test(NAME guest32_provider_experiments COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_provider_experiments.py" --build "${PROJECT_BINARY_DIR}"
    --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower> --execute)

# Explicit completion target. Each stage validates content receipts against the
# original sources, effective VFS dependencies, compiler and joint ABI catalog.
# It is intentionally separate from game admission and hardware validation.
set(guest32_provider_dir "${PROJECT_BINARY_DIR}/provider-closure170")
set(guest32_provider_outputs)
foreach(file IN ITEMS guest.ll frontend.log)
    set(paths ${hg_declared_guest_ir_objects})
    list(TRANSFORM paths PREPEND "${guest32_provider_dir}/")
    list(TRANSFORM paths APPEND "/${file}")
    list(APPEND guest32_provider_outputs ${paths})
endforeach()
foreach(file IN ITEMS abi.json native.ll
        lower.log native.o object.log provider.a)
    set(paths ${hg_declared_provider_objects})
    list(TRANSFORM paths PREPEND "${guest32_provider_dir}/")
    list(TRANSFORM paths APPEND "/${file}")
    list(APPEND guest32_provider_outputs ${paths})
endforeach()
foreach(file IN LISTS guest32_shared_outputs)
    # Publication invalidates stage-local command receipts when paths move.
    # They are cache metadata, not published outputs of the closure generation.
    if(file MATCHES "\\.receipt\\.json$" OR
       file STREQUAL "${guest32_shared_dir}/shared.d" OR
       file MATCHES "/OVY_[0-9]+/plan\\.json$")
        continue()
    endif()
    string(REPLACE "${guest32_shared_dir}" "${guest32_provider_dir}" file "${file}")
    list(APPEND guest32_provider_outputs "${file}")
endforeach()
# Production admission always rebuilds the current source selection. Historical
# recovery fixtures remain test inputs, never an implicit production build mode.
# Track the source inputs that can affect original game provider closure.
# CONFIGURE_DEPENDS discovers added and removed source files too.
file(GLOB_RECURSE guest32_closure_source_inputs
    CONFIGURE_DEPENDS
    "${game_source}/*.[chsS]"
    "${game_source}/*.cpp")

file(GLOB_RECURSE guest32_closure_tool_inputs
    CONFIGURE_DEPENDS
    "${PROJECT_SOURCE_DIR}/compiler/guest32/*.py")
list(APPEND guest32_closure_tool_inputs
    "${PROJECT_SOURCE_DIR}/cmake/native_sources.py"
    "${PROJECT_SOURCE_DIR}/cmake/native_pristine_compat.json"
    "${PROJECT_SOURCE_DIR}/cmake/guest32_closure.py")
list(APPEND guest32_closure_tool_inputs
    "${PROJECT_SOURCE_DIR}/cmake/native_overlay_link.py"
    "${PROJECT_SOURCE_DIR}/cmake/native_provider_registry.py")

add_test(NAME guest32_provider_frontend COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_provider_frontend.py"
    --build "${PROJECT_BINARY_DIR}" --llvm-bin "${guest32_tools}")
add_test(NAME guest32_discovery_reuse COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_provider_discovery.py"
    --build "${PROJECT_BINARY_DIR}" --clang "${guest32_tools}/clang"
    --lowerer $<TARGET_FILE:guest32-lower>)
add_test(NAME guest32_provider_batch COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_provider_batch.py"
    --build "${PROJECT_BINARY_DIR}" --clang "${guest32_tools}/clang"
    --lowerer $<TARGET_FILE:guest32-lower> --codegen $<TARGET_FILE:guest32-codegen>)
add_test(NAME guest32_provider_plan COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_provider_plan.py" --build "${PROJECT_BINARY_DIR}")
add_test(NAME guest32_provider_abi COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_provider_abi.py" --build "${PROJECT_BINARY_DIR}"
    --clang "${guest32_tools}/clang")

add_custom_command(OUTPUT "${guest32_provider_dir}/complete.stamp"
    COMMAND "${Python3_EXECUTABLE}" -B "${PROJECT_SOURCE_DIR}/compiler/guest32/finish.py"
        --game "${game_source}" --build "${PROJECT_BINARY_DIR}" --out "${guest32_provider_dir}"
        --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>
        --codegen $<TARGET_FILE:guest32-codegen>
        --image-root "${guest32_shared_dir}" --compiler "${CMAKE_C_COMPILER}"
        --root-symbol NitroMain --root-symbol CodeEntryArgs_New --root-symbol ListMenuInit
        --provider-plan "${PROJECT_SOURCE_DIR}/compiler/guest32/main_provider_plan.json"
    BYPRODUCTS ${guest32_provider_outputs}
        "${guest32_provider_dir}/discovery.json" "${guest32_provider_dir}/closure.json"
        "${guest32_provider_dir}/execution-plan.json"
        "${guest32_provider_dir}/provider-artifacts/symbol-inputs.json"
        "${guest32_provider_dir}/provider-artifacts/symbols.json"
        "${guest32_provider_dir}/thread-entry.json" "${guest32_provider_dir}/bindings.json"
        "${guest32_provider_dir}/providers.json" "${guest32_provider_dir}/runtime-providers.json"
        "${guest32_provider_dir}/catalog.json" "${guest32_provider_dir}/thread-entry.c"
        "${guest32_provider_dir}/compiler-catalog.json"
        "${guest32_provider_dir}/direct-catalog.json"
        "${guest32_provider_dir}/provider-profile.json" "${guest32_provider_dir}/finish-profile.json"
        "${guest32_provider_dir}/backend-profile.json"
        "${guest32_provider_dir}/thread-entry.o" "${guest32_provider_dir}/thread-entry.a"
        "${guest32_provider_dir}/frontend/lib/NitroSDK/src/os/os_alarm_before_handler.c"
        "${guest32_provider_dir}/frontend/lib/NitroSDK/src/os/os_alarm_after_handler.c"
        "${guest32_provider_dir}/links/symbol-inputs.json" "${guest32_provider_dir}/links/symbols.json"
        "${guest32_provider_dir}/links/OVY_0-global.dylib"
        "${guest32_provider_dir}/links/OVY_38-global.dylib"
    DEPENDS ${guest32_closure_source_inputs}
        "${PROJECT_SOURCE_DIR}/compiler/guest32/main_provider_plan.json"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/main_provider_abi.json.gz"
        ${guest32_closure_tool_inputs}
        guest32-lower guest32-codegen "${PROJECT_BINARY_DIR}/guest32-compiler/codegen-inputs.json"
        heartgold_guest32_shared heartgold_guest32_context heartgold_guest32_cache
        heartgold_guest32_account_build heartgold_guest32_crc_build heartgold_guest32_std_build
        heartgold_guest32_runtime heartgold_guest32_mi_manifest heartgold_guest32_scalar_bridges
        heartgold_guest32_libc_memory heartgold_overlay_link_contract
        "${game_source}/tools/alarm-partition/profile.json"
        "${game_source}/tools/alarm-partition/partition.py"
    VERBATIM)

add_custom_target(heartgold_guest32_provider_closure
    DEPENDS "${guest32_provider_dir}/complete.stamp")
add_test(NAME guest32_recovery_publication COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_recovery.py" --build "${PROJECT_BINARY_DIR}")
add_test(NAME guest32_absolute_overlay_ids COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_absolute_symbols.py"
    --build "${PROJECT_BINARY_DIR}" --llvm-bin "${guest32_tools}"
    --lowerer $<TARGET_FILE:guest32-lower>)
add_test(NAME guest32_effective_inputs COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_effective_inputs.py" --build "${PROJECT_BINARY_DIR}"
    --llvm-bin "${guest32_tools}")
add_test(NAME guest32_varargs_execution COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_varargs.py" --build "${PROJECT_BINARY_DIR}"
    --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>)
add_test(NAME guest32_original_execution COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_execution170.py" --build "${PROJECT_BINARY_DIR}"
    --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>)
set(guest32_execution_data_members
    lib/MSL_C/asm/MSL_Common_ctype.o lib/MSL_C/asm/MSL_Common_errno.o
    lib/asm/wifi_data.o lib/asm/wifi_bss.o)
set(guest32_execution_data_args)
set(guest32_execution_data_sources)
foreach(member IN LISTS guest32_execution_data_members)
    list(APPEND guest32_execution_data_args --member "${member}")
    string(REGEX REPLACE "\\.o$" ".s" relative "${member}")
    list(APPEND guest32_execution_data_sources "${game_source}/${relative}")
endforeach()
add_custom_command(OUTPUT "${guest32_provider_dir}/data/provider.a"
    "${guest32_provider_dir}/data/providers.json" "${guest32_provider_dir}/data/data.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${PROJECT_SOURCE_DIR}/compiler/guest32/data.py"
        --game "${game_source}" --out "${guest32_provider_dir}/data" --llvm-bin "${guest32_tools}"
        --owner main ${guest32_execution_data_args}
    DEPENDS ${guest32_execution_data_sources} "${game_source}/main.lsf"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/data.py"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/original_layout.py"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/original_data_layouts.json"
        "${PROJECT_SOURCE_DIR}/cmake/native_data_ir.py"
    VERBATIM)
add_custom_target(heartgold_guest32_execution_data DEPENDS "${guest32_provider_dir}/data/provider.a")
heartgold_test_fixture(guest32_execution_data heartgold_guest32_execution_data)
set_tests_properties(guest32_original_execution PROPERTIES FIXTURES_REQUIRED guest32_execution_data)

# Bind proven byte-compatible resident storage; never allocate a guest copy.
# This does not authorize image admission or entry wrappers for the blocked state.
set(hg_execution_dir "${PROJECT_BINARY_DIR}/execution-boundary")
add_custom_command(OUTPUT "${hg_execution_dir}/state/state.json"
        "${hg_execution_dir}/state/bindings.c"
        "${hg_execution_dir}/state/typed-bindings.c"
        "${hg_execution_dir}/state/typed-plans.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${PROJECT_SOURCE_DIR}/cmake/guest32_state.py"
        --build "${PROJECT_BINARY_DIR}" --closure "${guest32_provider_dir}"
        --game "${game_source}" --lowerer $<TARGET_FILE:guest32-lower>
        --out "${hg_execution_dir}/state"
    BYPRODUCTS "${hg_execution_dir}/state/state.d" "${hg_execution_dir}/state/storage-inputs.json"
        "${hg_execution_dir}/state/storage-contracts.json"
    DEPENDS heartgold_main heartgold_guest32_provider_closure
        "${PROJECT_SOURCE_DIR}/cmake/guest32_state.py"
        "${PROJECT_SOURCE_DIR}/cmake/guest32_sdk_storage.py"
        "${PROJECT_SOURCE_DIR}/cmake/guest32_typed_state.py"
    DEPFILE "${hg_execution_dir}/state/state.d"
    VERBATIM)
add_custom_target(heartgold_guest32_state_proof DEPENDS "${hg_execution_dir}/state/state.json"
    "${hg_execution_dir}/state/bindings.c" "${hg_execution_dir}/state/typed-bindings.c"
    "${hg_execution_dir}/state/typed-plans.json")
set_source_files_properties(
    "${hg_execution_dir}/state/bindings.c"
    "${hg_execution_dir}/state/typed-bindings.c"
    PROPERTIES GENERATED TRUE)
add_library(heartgold_guest32_main_state STATIC
    "${hg_execution_dir}/state/bindings.c"
    "${hg_execution_dir}/state/typed-bindings.c"
    "${PROJECT_SOURCE_DIR}/hardware_drivers/guest32_main_state.c")
target_include_directories(heartgold_guest32_main_state PRIVATE "${PROJECT_SOURCE_DIR}/hardware_drivers")
add_dependencies(heartgold_guest32_main_state heartgold_guest32_state_proof)
target_link_libraries(heartgold PRIVATE heartgold_guest32_main_state heartgold_guest32_runtime)
heartgold_test_fixture(execution_boundary heartgold_guest32_main_state)
add_test(NAME guest32_execution_boundary COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_guest32_execution_boundary.py"
    --build "${PROJECT_BINARY_DIR}" --game "${game_source}"
    --lowerer $<TARGET_FILE:guest32-lower> --llvm-bin "${guest32_tools}")
set_tests_properties(guest32_execution_boundary PROPERTIES FIXTURES_REQUIRED execution_boundary)

# Private address-identity hooks on the source-faithful u32 save marker.
set_property(SOURCE "${native_root}/src/system.c" APPEND PROPERTY
    INCLUDE_DIRECTORIES "${PROJECT_SOURCE_DIR}/hardware_drivers")
