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
        "${guest32_driver}" "${PROJECT_SOURCE_DIR}/compiler/guest32/ovy0_layout.json"
        "${game_source}/lib/NitroDWC/src/available_check_poll.alias-map.json"
    VERBATIM)
add_custom_target(heartgold_guest32_ovy0 DEPENDS "${guest32_image_dir}/complete.stamp")
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
