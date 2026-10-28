# Original HeartGold zone-event archive, compiled for DS data layout.

set(hg_zone_source
    "${game_source}/files/fielddata/eventdata/zone_event")
set(hg_zone_template
    "${game_source}/files/fielddata/eventdata/zone_event.json.txt")
set(hg_zone_build
    "${CMAKE_BINARY_DIR}/generated/zone_event")
set(hg_zone_archive
    "${CMAKE_BINARY_DIR}/generated/files/fielddata/eventdata/zone_event.narc")
set(hg_zone_index
    "${CMAKE_BINARY_DIR}/generated/files/fielddata/eventdata/zone_event.naix")

file(GLOB hg_zone_jsons CONFIGURE_DEPENDS
    "${hg_zone_source}/*.json")
list(SORT hg_zone_jsons)

list(LENGTH hg_zone_jsons hg_zone_count)

# Original archive member numbers must be contiguous.
set(hg_zone_expected_id 0)

foreach(json IN LISTS hg_zone_jsons)
    get_filename_component(stem "${json}" NAME_WE)

    if(NOT stem MATCHES "^[0-9][0-9][0-9]_")
        message(FATAL_ERROR "Invalid zone-event filename: ${stem}")
    endif()

    string(SUBSTRING "${stem}" 0 3 member_id)
    string(REGEX REPLACE "^0+" "" member_id "${member_id}")

    if(member_id STREQUAL "")
        set(member_id 0)
    endif()

    if(NOT member_id EQUAL hg_zone_expected_id)
        message(FATAL_ERROR
            "Zone-event archive member mismatch at ${stem}; "
            "expected ${hg_zone_expected_id}")
    endif()

    math(EXPR hg_zone_expected_id "${hg_zone_expected_id} + 1")
endforeach()

set(hg_zone_binaries)

foreach(json IN LISTS hg_zone_jsons)
    get_filename_component(stem "${json}" NAME_WE)

    set(bin "${hg_zone_build}/${stem}.bin")
    set(dep "${hg_zone_build}/${stem}.d")

    add_custom_command(
        OUTPUT "${bin}"
        BYPRODUCTS
            "${hg_zone_build}/${stem}.s"
            "${hg_zone_build}/${stem}.o"

        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/cmake/build_zone_event.py"
            --source "${json}"
            --template "${hg_zone_template}"
            --output-dir "${hg_zone_build}"
            --jsonproc "$<TARGET_FILE:hg_jsonproc>"
            --clang "${CMAKE_C_COMPILER}"
            --objcopy "${HG_ASSET_OBJCOPY}"
            --readelf "${HG_ASSET_READELF}"
            --game "${game_source}"
            --libntr "${ntr_source}"

        DEPENDS
            hg_jsonproc
            "${json}"
            "${hg_zone_template}"
            "${CMAKE_CURRENT_SOURCE_DIR}/cmake/build_zone_event.py"

        DEPFILE "${dep}"
        VERBATIM
    )

    list(APPEND hg_zone_binaries "${bin}")
endforeach()

# Preserve original Nitroarc directory exclusions.
set(hg_zone_metadata)

foreach(meta IN ITEMS .narcorder .narcignore)
    if(EXISTS "${hg_zone_source}/${meta}")
        configure_file(
            "${hg_zone_source}/${meta}"
            "${hg_zone_build}/${meta}"
            COPYONLY)
        list(APPEND hg_zone_metadata "${hg_zone_build}/${meta}")
    endif()
endforeach()

add_custom_command(
    OUTPUT "${hg_zone_archive}" "${hg_zone_index}"

    COMMAND "${CMAKE_COMMAND}" -E make_directory
        "${CMAKE_BINARY_DIR}/generated/files/fielddata/eventdata"

    COMMAND $<TARGET_FILE:hg_nitroarc>
        -cf "${hg_zone_archive}"
        --index-namespace "${hg_zone_build}"

    DEPENDS
        hg_nitroarc
        ${hg_zone_binaries}
        ${hg_zone_metadata}

    VERBATIM
)

add_custom_target(heartgold_zone_event_assets
    DEPENDS "${hg_zone_archive}" "${hg_zone_index}")


message(STATUS
    "HeartGold: ${hg_zone_count} original zone-event members configured")
