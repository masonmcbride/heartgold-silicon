# Original field and battle script bytecode, using one assembler pipeline.
foreach(hg_script_archive fielddata/script/scr_seq battledata/script/move_script battledata/script/subscript)
get_filename_component(hg_script_name "${hg_script_archive}" NAME)

set(hg_script_source
    "${game_source}/files/${hg_script_archive}")
set(hg_script_stage
    "${PROJECT_BINARY_DIR}/generated/${hg_script_name}_archive")
set(hg_script_work
    "${PROJECT_BINARY_DIR}/generated/${hg_script_name}_work")

file(GLOB hg_script_sources CONFIGURE_DEPENDS
    "${hg_script_source}/*.s")
list(SORT hg_script_sources)

list(LENGTH hg_script_sources hg_script_count)
set(expected_script_id 0)

foreach(source IN LISTS hg_script_sources)
    get_filename_component(stem "${source}" NAME_WE)

    if(NOT stem MATCHES "^${hg_script_name}_([0-9][0-9][0-9][0-9])(_[A-Za-z0-9_]+)?$")
        message(FATAL_ERROR "Unexpected script source: ${stem}")
    endif()

    string(REGEX REPLACE "^0+" "" id "${CMAKE_MATCH_1}")
    if(id STREQUAL "")
        set(id 0)
    endif()

    if(NOT id EQUAL expected_script_id)
        message(FATAL_ERROR
            "Script ID mismatch: expected ${expected_script_id}, "
            "found ${stem}. Verify the original NARC member order.")
    endif()

    math(EXPR expected_script_id "${expected_script_id} + 1")
endforeach()

set(hg_script_bins)

foreach(source IN LISTS hg_script_sources)
    get_filename_component(stem "${source}" NAME_WE)
    set(bin "${hg_script_stage}/${stem}.bin")
    set(dep "${hg_script_work}/${stem}.d")

    add_custom_command(
        OUTPUT "${bin}"
        BYPRODUCTS "${hg_script_work}/${stem}.o"

        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_LIST_DIR}/build_heartgold_script.py"
            --source "${source}"
            --binary "${bin}"
            --work-dir "${hg_script_work}"
            --game "${game_source}"
            --libntr "${ntr_source}"
            --generated-files "${PROJECT_BINARY_DIR}/generated/files"
            --clang "${CMAKE_C_COMPILER}"
            --objcopy "${HG_ASSET_OBJCOPY}"
            --readelf "${HG_ASSET_READELF}"

        DEPENDS
            "${source}"
            "${CMAKE_CURRENT_LIST_DIR}/build_heartgold_script.py"

        DEPFILE "${dep}"
        VERBATIM
    )

    list(APPEND hg_script_bins "${bin}")
endforeach()

hg_narc(heartgold_${hg_script_name}_assets "${hg_script_archive}"
    "${hg_script_stage}" ${hg_script_bins})

add_dependencies(heartgold_${hg_script_name}_assets heartgold_msg_assets)

message(STATUS
    "HeartGold: ${hg_script_count} original scripts configured")

endforeach()
add_custom_target(heartgold_script_assets DEPENDS heartgold_scr_seq_assets heartgold_move_script_assets heartgold_subscript_assets)
