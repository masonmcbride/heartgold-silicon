# Whole original member, isolated until WM's guest32 providers are resolved.
set(wm_guest32_dir "${PROJECT_BINARY_DIR}/wm-guest32")
set(wm_guest32_driver "${CMAKE_CURRENT_LIST_DIR}/wm_guest32.py")
add_custom_command(OUTPUT "${wm_guest32_dir}/complete.stamp"
    BYPRODUCTS "${wm_guest32_dir}/wm_requests.o"
        "${wm_guest32_dir}/wm_guest32_layout.h" "${wm_guest32_dir}/wm_guest32_api.h"
        "${wm_guest32_dir}/layout-probe.c" "${wm_guest32_dir}/layout32.log"
        "${wm_guest32_dir}/layout64.log" "${wm_guest32_dir}/assertions.c"
        "${wm_guest32_dir}/original.ll" "${wm_guest32_dir}/lowered.ll"
        "${wm_guest32_dir}/abi.json" "${wm_guest32_dir}/native.ll"
        "${wm_guest32_dir}/commands.json" "${wm_guest32_dir}/evidence.json"
        "${wm_guest32_dir}/field-table.md"
        "${wm_guest32_dir}/definitions.txt" "${wm_guest32_dir}/imports.txt"
    COMMAND "${Python3_EXECUTABLE}" -B "${wm_guest32_driver}"
        --game "${game_source}" --build "${PROJECT_BINARY_DIR}"
        --out "${wm_guest32_dir}" --llvm-bin "${guest32_tools}"
        --lowerer $<TARGET_FILE:guest32-lower>
    DEPENDS guest32-lower fx_constants "${wm_guest32_driver}"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/frontend.py"
        "${game_source}/lib/NitroSDK/src/wm_requests.c"
        "${game_source}/lib/include/nitro/wm/wm_internal.h"
    DEPFILE "${wm_guest32_dir}/wm.d" VERBATIM)
add_custom_target(heartgold_wm_guest32_sources DEPENDS "${wm_guest32_dir}/complete.stamp")
add_custom_command(OUTPUT "${wm_guest32_dir}/providers.stamp"
    BYPRODUCTS "${wm_guest32_dir}/wm_core.o" "${wm_guest32_dir}/core.ll"
        "${wm_guest32_dir}/core.native.ll" "${wm_guest32_dir}/core.json"
        "${wm_guest32_dir}/core-catalog.json" "${wm_guest32_dir}/providers.json"
        "${wm_guest32_dir}/provider-commands.json" "${wm_guest32_dir}/state-template.h"
        "${wm_guest32_dir}/core-definitions.txt" "${wm_guest32_dir}/core-imports.txt"
    COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_LIST_DIR}/wm_guest32_providers.py"
        --game "${game_source}" --build "${PROJECT_BINARY_DIR}" --out "${wm_guest32_dir}"
        --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>
    DEPENDS "${wm_guest32_dir}/complete.stamp" guest32-lower
        "${CMAKE_CURRENT_LIST_DIR}/wm_guest32_providers.py"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/code_ids.py"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/frontend.py"
        "${game_source}/lib/NitroSDK/src/wm_core.c"
        "${game_source}/lib/asm/nitro_sdk_data.s"
    DEPFILE "${wm_guest32_dir}/core.d" VERBATIM)
add_custom_target(heartgold_wm_guest32_providers DEPENDS "${wm_guest32_dir}/providers.stamp")
set_source_files_properties("${wm_guest32_dir}/wm_requests.o" PROPERTIES
    GENERATED TRUE EXTERNAL_OBJECT TRUE)
set_source_files_properties("${wm_guest32_dir}/wm_core.o" PROPERTIES
    GENERATED TRUE EXTERNAL_OBJECT TRUE)
add_library(heartgold_wm_guest32_audit STATIC EXCLUDE_FROM_ALL
    "${wm_guest32_dir}/wm_requests.o" "${wm_guest32_dir}/wm_core.o")
set_target_properties(heartgold_wm_guest32_audit PROPERTIES LINKER_LANGUAGE C)
add_dependencies(heartgold_wm_guest32_audit heartgold_wm_guest32_sources heartgold_wm_guest32_providers)
add_library(heartgold_wm_guest32_services STATIC EXCLUDE_FROM_ALL
    "${PROJECT_SOURCE_DIR}/hardware_drivers/wireless/wm_guest32_services.c")
target_include_directories(heartgold_wm_guest32_services PRIVATE "${wm_guest32_dir}")
target_link_libraries(heartgold_wm_guest32_services PRIVATE nitro_sdk)
add_dependencies(heartgold_wm_guest32_services heartgold_wm_guest32_sources)
add_executable(test_wm_guest32_services EXCLUDE_FROM_ALL
    "${PROJECT_SOURCE_DIR}/tests/test_wm_guest32_services.c"
    "${PROJECT_SOURCE_DIR}/hardware_drivers/guest32.c")
target_include_directories(test_wm_guest32_services PRIVATE
    "${PROJECT_SOURCE_DIR}/hardware_drivers" "${wm_guest32_dir}")
target_link_libraries(test_wm_guest32_services PRIVATE heartgold_wm_guest32_services)
target_compile_options(test_wm_guest32_services PRIVATE -UNDEBUG
    -fsanitize=address,undefined -fno-sanitize-recover=all)
target_link_options(test_wm_guest32_services PRIVATE -fsanitize=address,undefined)
add_dependencies(test_wm_guest32_services heartgold_wm_guest32_sources)
add_test(NAME wm_guest32_build COMMAND "${CMAKE_COMMAND}" --build "${PROJECT_BINARY_DIR}"
    --target heartgold_wm_guest32_audit test_wm_guest32_services -j8)
set_tests_properties(wm_guest32_build PROPERTIES FIXTURES_SETUP wm_guest32)
add_test(NAME wm_guest32 COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_wm_guest32.py"
    --build "${PROJECT_BINARY_DIR}" --llvm-bin "${guest32_tools}"
    --lowerer $<TARGET_FILE:guest32-lower>)
set_tests_properties(wm_guest32 PROPERTIES FIXTURES_REQUIRED wm_guest32)
add_test(NAME wm_guest32_services COMMAND test_wm_guest32_services)
set_tests_properties(wm_guest32_services PROPERTIES FIXTURES_REQUIRED wm_guest32)
add_test(NAME wm_guest32_provider_gate COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_wm_guest32_providers.py"
    --build "${PROJECT_BINARY_DIR}" --llvm-bin "${guest32_tools}"
    --lowerer $<TARGET_FILE:guest32-lower>)
set_tests_properties(wm_guest32_provider_gate PROPERTIES FIXTURES_REQUIRED wm_guest32)
