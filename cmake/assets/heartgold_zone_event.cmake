# Original HeartGold zone-event archive, compiled for DS data layout.

set(hg_zone_source
    "${game_source}/files/fielddata/eventdata/zone_event")
set(hg_zone_template
    "${game_source}/files/fielddata/eventdata/zone_event.json.txt")
set(hg_zone_build
    "${PROJECT_BINARY_DIR}/generated/zone_event")

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

set(hg_asset_batch_dependencies hg_jsonproc "${hg_zone_template}")
hg_native_asset_data("Map interactions" zone "${hg_zone_build}" "${hg_zone_build}" "${hg_zone_jsons}"
    --template "${hg_zone_template}" --jsonproc "$<TARGET_FILE:hg_jsonproc>"
    --clang "${CMAKE_C_COMPILER}" --objcopy "${HG_ASSET_OBJCOPY}" --readelf "${HG_ASSET_READELF}"
    --game "${game_source}" --libntr "${ntr_source}")
foreach(json IN LISTS hg_zone_jsons)
    get_filename_component(stem "${json}" NAME_WE)
    list(APPEND hg_zone_binaries "${hg_zone_build}/${stem}.bin")
endforeach()

hg_ordered_archive(heartgold_zone_event_assets "fielddata/eventdata/zone_event"
    "${hg_zone_build}" ${hg_zone_binaries})

message(STATUS
    "HeartGold: Map interactions - ${hg_zone_count} map-event layouts configured (NPC/object placement, door and stair warps, signs and coordinate triggers)")
