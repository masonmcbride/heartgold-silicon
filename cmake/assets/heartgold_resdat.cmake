# Original sprite resource JSON/C data, compiled with its fixed DS record layout.
set(hg_resdat_source "${game_source}/files/data/resdat")
set(hg_resdat_template "${game_source}/files/data/resdat.json.txt")
set(hg_resdat_work "${PROJECT_BINARY_DIR}/generated/resdat")
set(hg_resdat_members "${PROJECT_BINARY_DIR}/generated/files/data/resdat")
set(hg_resdat_types "${hg_resdat_work}/resdat_types.h")
native_generate(resdat-types "${game_source}/include/sprite_resource.h" "${hg_resdat_types}"
    "${game_source}/include/sprite_resource_header.h")

file(GLOB hg_resdat_jsons CONFIGURE_DEPENDS "${hg_resdat_source}/*.json")
list(SORT hg_resdat_jsons)
list(LENGTH hg_resdat_jsons hg_resdat_count)
if(NOT hg_resdat_count EQUAL 90)
    message(FATAL_ERROR "Expected 90 original Resdat files, found ${hg_resdat_count}")
endif()
set(hg_resdat_bins)
set(hg_resdat_expected 0)
foreach(json IN LISTS hg_resdat_jsons)
    get_filename_component(stem "${json}" NAME_WE)
    if(NOT stem MATCHES "^resdat_[0-9]+$")
        message(FATAL_ERROR "Unexpected Resdat filename: ${stem}")
    endif()
    string(REGEX REPLACE "^resdat_0*" "" id "${stem}")
    if(id STREQUAL "")
        set(id 0)
    endif()
    if(NOT id EQUAL hg_resdat_expected)
        message(FATAL_ERROR "Non-contiguous Resdat member: ${stem}")
    endif()
    math(EXPR hg_resdat_expected "${hg_resdat_expected} + 1")
    set(c "${hg_resdat_work}/${stem}.c")
    set(obj "${hg_resdat_work}/${stem}.o")
    set(bin "${hg_resdat_members}/${stem}.bin")
    set(dep "${hg_resdat_work}/${stem}.d")
    # Original JSON -> generated C -> original ARM data object -> binary.
    # Each generated artifact has exactly one producing build edge.
    add_custom_command(OUTPUT "${c}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_resdat_work}"
        COMMAND $<TARGET_FILE:hg_jsonproc> "${json}" "${hg_resdat_template}" "${c}"
        DEPENDS hg_jsonproc "${json}" "${hg_resdat_template}"
        VERBATIM)

    add_custom_command(OUTPUT "${obj}"
        COMMAND "${CMAKE_C_COMPILER}" --target=armv5te-none-eabi -std=gnu11 -fdata-sections
            -DPOKEHEARTGOLD_GLOBAL_H -DPOKEHEARTGOLD_SPRITE_RESOURCE_HEADER_H -DNITRO_FS_FILE_H_
            -include "${hg_resdat_types}" -I "${game_source}/include" -I "${game_source}/lib/include"
            -MMD -MF "${dep}" -MQ "${obj}" -c "${c}" -o "${obj}"
        DEPENDS "${c}" "${hg_resdat_types}"
        DEPFILE "${dep}"
        VERBATIM)

    add_custom_command(OUTPUT "${bin}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_resdat_members}"
        COMMAND "${HG_ASSET_OBJCOPY}" -O binary --only-section=.rodata.data "${obj}" "${bin}"
        DEPENDS "${obj}"
        VERBATIM)
    list(APPEND hg_resdat_bins "${bin}")
endforeach()
hg_narc(heartgold_resdat_assets "data/resdat" "${hg_resdat_members}" ${hg_resdat_bins})
