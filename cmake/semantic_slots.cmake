# Whole-production native IR constraints. Guest32 keeps its original DS layout.
set(hg_slot_dir "${PROJECT_BINARY_DIR}/semantic-slots")
set(hg_slot_driver "${PROJECT_SOURCE_DIR}/compiler/guest32/semantic_slots.py")
set(hg_slot_targets heartgold_main hg_dwc_status_code hg_dwc_main hg_ovy0_wifi_code)
foreach(id IN LISTS hg_selected_overlay_ids)
    list(APPEND hg_slot_targets "${hg_overlay_${id}_archive}")
endforeach()
list(REMOVE_DUPLICATES hg_slot_targets)
set(hg_slot_outputs)
set(hg_slot_members)
set(hg_slot_sources)
set(hg_slot_approvals)
foreach(target IN LISTS hg_slot_targets)
    get_target_property(sources ${target} SOURCES)
    foreach(source IN LISTS sources)
        if(source MATCHES "\\.(c|cpp|cc)$")
            get_filename_component(source_abs "${source}" ABSOLUTE BASE_DIR "${PROJECT_SOURCE_DIR}")
            list(APPEND hg_slot_sources "${source_abs}")
            string(SHA256 member "${target}|${source_abs}")
            list(APPEND hg_slot_approvals "${hg_slot_dir}/members/${member}/codegen.json")
            list(APPEND hg_slot_members "${hg_slot_dir}/members/${member}")
        endif()
    endforeach()
endforeach()
# promoted.ll is conditional on the analysis selecting a transformation. Its
# consumers track it through their per-object approvals and compiler depfiles.
# Declaring it for unchanged modules makes every subsequent Ninja run dirty.
foreach(file original.bc original.d receipt.json frontend.log frontend-time-trace.json)
    set(paths ${hg_slot_members})
    list(TRANSFORM paths APPEND "/${file}")
    list(APPEND hg_slot_outputs ${paths})
endforeach()
list(REMOVE_DUPLICATES hg_slot_approvals)
list(REMOVE_DUPLICATES hg_slot_sources)
add_custom_command(OUTPUT "${hg_slot_dir}/complete.stamp"
    BYPRODUCTS "${hg_slot_dir}/plan.json" "${hg_slot_dir}/registry.json"
        "${hg_slot_dir}/profile.json"
        "${hg_slot_dir}/analysis-receipt.json"
        "${hg_slot_dir}/plan.pending.json.profile.json"
        "${hg_slot_dir}/inputs.json" "${hg_slot_dir}/plan.pending.json"
        "${hg_slot_dir}/census.lock" ${hg_slot_outputs}
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_slot_driver}"
        --build "${PROJECT_BINARY_DIR}" --lowerer $<TARGET_FILE:guest32-lower>
    DEPENDS guest32-lower "${hg_slot_driver}" "${PROJECT_BINARY_DIR}/compile_commands.json"
        "${PROJECT_SOURCE_DIR}/compiler/guest32/incremental.py"
        ${hg_slot_sources}
        "${PROJECT_SOURCE_DIR}/compiler/guest32/semantic_slot_lifetimes.json"
        heartgold_native_headers heartgold_overlay_native_sources
        fx_constants ${heartgold_compile_asset_targets}
    DEPFILE "${hg_slot_dir}/census.d"
    VERBATIM)
add_custom_target(heartgold_semantic_slots DEPENDS "${hg_slot_dir}/complete.stamp")
# One bulk metadata check replaces a separate Make rule for every unit. It
# repairs missing records before objects are visited and preserves valid mtimes.
add_custom_target(heartgold_semantic_slot_approvals
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_slot_driver}" ensure "${hg_slot_dir}/registry.json"
    BYPRODUCTS ${hg_slot_approvals}
    DEPENDS heartgold_semantic_slots VERBATIM)
foreach(target IN LISTS hg_slot_targets)
    add_dependencies(${target} heartgold_semantic_slot_approvals)
    set_property(TARGET ${target} PROPERTY C_COMPILER_LAUNCHER
        "${Python3_EXECUTABLE};-B;${hg_slot_driver};launch;${hg_slot_dir}/registry.json")
    set_property(TARGET ${target} PROPERTY CXX_COMPILER_LAUNCHER
        "${Python3_EXECUTABLE};-B;${hg_slot_driver};launch;${hg_slot_dir}/registry.json")
endforeach()
add_test(NAME semantic_pointer_slots COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_semantic_slots.py" --build "${PROJECT_BINARY_DIR}"
    --lowerer $<TARGET_FILE:guest32-lower> --llvm-bin "${guest32_tools}")
heartgold_test_fixture(semantic_slots_production heartgold_main heartgold_overlay_12 heartgold_image_1)
set_tests_properties(semantic_pointer_slots PROPERTIES FIXTURES_REQUIRED semantic_slots_production)
add_test(NAME native_codegen_dependencies COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_codegen_dependencies.py" --build "${PROJECT_BINARY_DIR}"
    --lowerer $<TARGET_FILE:guest32-lower>)
