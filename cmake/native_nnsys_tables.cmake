# Original NitroSystem data: single producer and runtime owner.
include_guard(GLOBAL)

# Original producer + texture-matrix closure; no gecom transport or renderer.
set(g3_probe_tables "${PROJECT_BINARY_DIR}/g3-probe/nnsys_tables.c")
set(g3_probe_script "${CMAKE_CURRENT_LIST_DIR}/native_sources.py")
add_custom_command(OUTPUT "${g3_probe_tables}"
    COMMAND "${Python3_EXECUTABLE}" -B "${g3_probe_script}" --root "${game_source}"
        --kind g3-probe-tables --input "${game_source}/lib/asm/nnsys_data.s"
        --output "${g3_probe_tables}"
    COMMAND "${CMAKE_COMMAND}" -E touch_nocreate "${g3_probe_tables}"
    DEPENDS "${g3_probe_script}" "${CMAKE_CURRENT_LIST_DIR}/native_coordinated.py"
        "${game_source}/lib/asm/nnsys_data.s" VERBATIM)
add_custom_target(heartgold_g3_probe_tables DEPENDS "${g3_probe_tables}")

if(TARGET heartgold_runtime)
    # Reuse one deterministic native output for this original assembly input.
    # Its original main-owned callback globals also serve native overlay imports.
    add_dependencies(heartgold_runtime heartgold_g3_probe_tables)
    target_sources(heartgold_runtime PRIVATE "${g3_probe_tables}")
    target_compile_definitions(heartgold_runtime PRIVATE HG_NATIVE_NNSYS_DATA)
    target_include_directories(heartgold_runtime PRIVATE "${PROJECT_BINARY_DIR}/native/lib/include")
    target_compile_options(heartgold_runtime PRIVATE "-idirafter${game_source}/lib/include")
endif()
