# Whole-production native IR constraints. Guest32 keeps its original DS layout.
set(hg_slot_dir "${PROJECT_BINARY_DIR}/semantic-slots")
set(hg_slot_driver "${PROJECT_SOURCE_DIR}/compiler/guest32/semantic_slots.py")
set(hg_slot_targets heartgold_main hg_dwc_status_code hg_dwc_main hg_ovy0_wifi_code)
foreach(id IN LISTS hg_selected_overlay_ids)
    list(APPEND hg_slot_targets "${hg_overlay_${id}_archive}")
endforeach()
list(REMOVE_DUPLICATES hg_slot_targets)
set(hg_slot_outputs)
foreach(target IN LISTS hg_slot_targets)
    get_target_property(sources ${target} SOURCES)
    foreach(source IN LISTS sources)
        if(source MATCHES "\\.(c|cpp|cc)$")
            get_filename_component(source_abs "${source}" ABSOLUTE BASE_DIR "${PROJECT_SOURCE_DIR}")
            string(SHA256 member "${target}|${source_abs}")
            foreach(file original.ll original.d receipt.json frontend.log promoted.ll)
                list(APPEND hg_slot_outputs "${hg_slot_dir}/members/${member}/${file}")
            endforeach()
        endif()
    endforeach()
endforeach()
add_custom_command(OUTPUT "${hg_slot_dir}/complete.stamp"
    BYPRODUCTS "${hg_slot_dir}/plan.json" "${hg_slot_dir}/registry.json"
        "${hg_slot_dir}/inputs.json" "${hg_slot_dir}/plan.pending.json"
        "${hg_slot_dir}/census.lock" ${hg_slot_outputs}
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_slot_driver}"
        --build "${PROJECT_BINARY_DIR}" --lowerer $<TARGET_FILE:guest32-lower>
    DEPENDS guest32-lower "${hg_slot_driver}" "${PROJECT_BINARY_DIR}/compile_commands.json"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/semantic_slot_lifetimes.json"
        heartgold_native_headers heartgold_overlay_native_sources
        fx_constants ${heartgold_asset_targets}
    DEPFILE "${hg_slot_dir}/census.d"
    VERBATIM)
add_custom_target(heartgold_semantic_slots DEPENDS "${hg_slot_dir}/complete.stamp")
foreach(target IN LISTS hg_slot_targets)
    add_dependencies(${target} heartgold_semantic_slots)
    set_property(TARGET ${target} PROPERTY C_COMPILER_LAUNCHER
        "${Python3_EXECUTABLE};-B;${hg_slot_driver};launch;${hg_slot_dir}/registry.json")
    set_property(TARGET ${target} PROPERTY CXX_COMPILER_LAUNCHER
        "${Python3_EXECUTABLE};-B;${hg_slot_driver};launch;${hg_slot_dir}/registry.json")
    get_target_property(sources ${target} SOURCES)
    foreach(source IN LISTS sources)
        if(source MATCHES "\\.(c|cpp|cc)$")
            set_property(SOURCE "${source}" APPEND PROPERTY OBJECT_DEPENDS "${hg_slot_dir}/plan.json")
        endif()
    endforeach()
endforeach()
add_test(NAME semantic_pointer_slots COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_semantic_slots.py" --build "${PROJECT_BINARY_DIR}"
    --lowerer $<TARGET_FILE:guest32-lower> --llvm-bin "${guest32_tools}")
add_test(NAME semantic_pointer_slots_build COMMAND "${CMAKE_COMMAND}" --build "${PROJECT_BINARY_DIR}"
    --target heartgold_main heartgold_overlay_12 heartgold_image_1 -j8)
set_tests_properties(semantic_pointer_slots_build PROPERTIES FIXTURES_SETUP semantic_slots_production)
set_tests_properties(semantic_pointer_slots PROPERTIES FIXTURES_REQUIRED semantic_slots_production)
