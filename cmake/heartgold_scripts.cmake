# Original HeartGold script-bytecode archive.

set(hg_script_source
    "${game_source}/files/fielddata/script/scr_seq")
set(hg_script_stage
    "${CMAKE_BINARY_DIR}/generated/scr_seq_archive")
set(hg_script_work
    "${CMAKE_BINARY_DIR}/generated/scr_seq_work")
set(hg_script_narc
    "${CMAKE_BINARY_DIR}/generated/files/fielddata/script/scr_seq.narc")
set(hg_script_naix
    "${CMAKE_BINARY_DIR}/generated/files/fielddata/script/scr_seq.naix")

file(GLOB hg_script_sources CONFIGURE_DEPENDS
    "${hg_script_source}/*.s")
list(SORT hg_script_sources)

list(LENGTH hg_script_sources hg_script_count)
set(expected_script_id 0)

foreach(source IN LISTS hg_script_sources)
    get_filename_component(stem "${source}" NAME_WE)

    if(NOT stem MATCHES "^scr_seq_([0-9][0-9][0-9][0-9])(_[A-Za-z0-9_]+)?$")
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
            --generated-files "${CMAKE_BINARY_DIR}/generated/files"
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

set(hg_script_metadata)

foreach(meta IN ITEMS .narcorder .narcignore)
    if(EXISTS "${hg_script_source}/${meta}")
        configure_file(
            "${hg_script_source}/${meta}"
            "${hg_script_stage}/${meta}"
            COPYONLY)
        list(APPEND hg_script_metadata
            "${hg_script_stage}/${meta}")
    endif()
endforeach()

add_custom_command(
    OUTPUT "${hg_script_narc}" "${hg_script_naix}"

    COMMAND "${CMAKE_COMMAND}" -E make_directory
        "${CMAKE_BINARY_DIR}/generated/files/fielddata/script"

    COMMAND $<TARGET_FILE:hg_nitroarc>
        -cf "${hg_script_narc}"
        --index-namespace "${hg_script_stage}"

    DEPENDS hg_nitroarc ${hg_script_bins} ${hg_script_metadata}
    VERBATIM
)

add_custom_target(heartgold_script_assets
    DEPENDS "${hg_script_narc}" "${hg_script_naix}")

add_dependencies(heartgold_script_assets heartgold_msg_assets)

message(STATUS
    "HeartGold: ${hg_script_count} original scripts configured")
