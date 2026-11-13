include("${CMAKE_CURRENT_LIST_DIR}/native_nnsys_tables.cmake")

# Reuse the existing declaration-only adaptation and its single output.
set(g3_probe_header "${PROJECT_BINARY_DIR}/native/lib/include/nnsys/g3d_render_internal.h")
if(NOT TARGET heartgold_native_headers)
    add_custom_command(OUTPUT "${g3_probe_header}"
        COMMAND "${Python3_EXECUTABLE}" -B "${g3_probe_script}" --root "${game_source}"
            --input "${game_source}/lib/include/nnsys/g3d_render_internal.h"
            --output "${g3_probe_header}"
        DEPENDS "${g3_probe_script}" "${game_source}/lib/include/nnsys/g3d_render_internal.h"
        VERBATIM)
endif()
set(g3_probe_sources g3d_1mat1shp.c g3d_cgtool_maya_tex.c
    gfd_tex_vram_man.c gfd_pltt_vram_man.c
    g3d_cgtool_maya_texmtx.c g3d_cgtool_maya_texmtx_r.c g3d_cgtool_maya_texmtx_s.c
    g3d_cgtool_si3d.c g3d_cgtool_3dsmax.c g3d_cgtool_3dsmax_texmtx.c
    g3d_cgtool_xsi.c g3d_cgtool_xsi_texmtx.c g3d_cgtool_xsi_texmtx_sr.c
    g3d_cgtool_xsi_texmtx_t.c)
list(TRANSFORM g3_probe_sources PREPEND "${game_source}/lib/NitroSystem/src/")
add_executable(g3_emit_probe tests/g3_emit_probe.c ${g3_probe_sources}
    "${g3_probe_tables}" "${g3_probe_header}")
if(TARGET heartgold_native_headers)
    add_dependencies(g3_emit_probe heartgold_native_headers)
endif()
target_link_libraries(g3_emit_probe PRIVATE nitro_config ntr_fx ntr_sim_state)
target_include_directories(g3_emit_probe BEFORE PRIVATE "${PROJECT_BINARY_DIR}/native/lib/include")
target_compile_options(g3_emit_probe PRIVATE "-idirafter${game_source}/lib/include"
    -fsanitize=address,undefined -fno-sanitize-recover=all)
target_link_options(g3_emit_probe PRIVATE -Wl,-dead_strip
    -fsanitize=address,undefined)
add_dependencies(g3_emit_probe fx_constants heartgold_g3_probe_tables)
add_test(NAME g3_emission COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_g3_emission.py" --probe $<TARGET_FILE:g3_emit_probe>
    --source "${PROJECT_SOURCE_DIR}" --work "${PROJECT_BINARY_DIR}/g3-probe")
set_tests_properties(g3_emission PROPERTIES TIMEOUT 30 ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0")

if(TARGET heartgold_runtime)
    add_executable(test_gfd_storage "${PROJECT_SOURCE_DIR}/tests/test_gfd_storage.c")
    target_link_libraries(test_gfd_storage PRIVATE heartgold_main nitro_sdk)
    target_compile_options(test_gfd_storage PRIVATE -UNDEBUG "-idirafter${game_source}/lib/include")
    target_link_options(test_gfd_storage PRIVATE -Wl,-dead_strip)
    add_test(NAME gfd_native_storage COMMAND test_gfd_storage)
endif()

# Separate execution consumer; the emission observer retains its original role.
add_executable(test_g3_native_model "${PROJECT_SOURCE_DIR}/tests/test_g3_native_model.cpp")
target_link_libraries(test_g3_native_model PRIVATE nitro_sdk)
target_compile_options(test_g3_native_model PRIVATE -UNDEBUG)
add_test(NAME native_g3_original_model COMMAND test_g3_native_model
    "${PROJECT_BINARY_DIR}/g3-probe/crystal-1.bin"
    "${PROJECT_BINARY_DIR}/g3-probe/crystal-metal.ppm")
set_tests_properties(g3_emission PROPERTIES FIXTURES_SETUP native_g3_original_emission)
set_tests_properties(native_g3_original_model PROPERTIES DEPENDS g3_emission
    FIXTURES_REQUIRED native_g3_original_emission TIMEOUT 30)
