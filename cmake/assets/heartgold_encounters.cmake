# Original JSONPROC data, native layout-checked emission, original Nitroarc.

set(hg_encounter_source "${game_source}/files/fielddata/encountdata")
set(hg_encounter_json "${hg_encounter_source}/gs_enc_data.json")
set(hg_encounter_template "${hg_encounter_source}/gs_enc_data.json.txt")
set(hg_encounter_build "${PROJECT_BINARY_DIR}/generated/encountdata")
set(hg_encounter_archive_dir "${PROJECT_BINARY_DIR}/generated/files/fielddata/encountdata")
set(hg_encounter_c "${hg_encounter_build}/gs_enc_data.c")
set(hg_encounter_emitter "${CMAKE_CURRENT_LIST_DIR}/heartgold_encounters.c")
set(hg_encounter_validator "${CMAKE_CURRENT_LIST_DIR}/validate_heartgold_encounters.py")

add_custom_command(
    OUTPUT "${hg_encounter_c}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_encounter_build}"
    COMMAND $<TARGET_FILE:hg_jsonproc>
        "${hg_encounter_json}" "${hg_encounter_template}" "${hg_encounter_c}"
    DEPENDS hg_jsonproc "${hg_encounter_json}" "${hg_encounter_template}"
    VERBATIM)

add_custom_target(hg_encounter_data DEPENDS "${hg_encounter_c}")

set(hg_encounter_archives)
foreach(version IN ITEMS g s)
    if(version STREQUAL "g")
        set(variant ENC_HEARTGOLD)
    else()
        set(variant ENC_SOULSILVER)
    endif()

    set(emitter hg_encounters_${version})
    set(stage "${hg_encounter_build}/${version}")
    add_executable(${emitter} "${hg_encounter_emitter}")
    add_dependencies(${emitter} hg_encounter_data)
    target_link_libraries(${emitter} PRIVATE nitro_config)
    target_compile_definitions(${emitter} PRIVATE SDK_DATA_ONLY ${variant})
    target_include_directories(${emitter} PRIVATE "${game_source}/include" "${hg_encounter_build}")
    set(narc "${hg_encounter_archive_dir}/${version}_enc_data.narc")
    set(naix "${hg_encounter_archive_dir}/${version}_enc_data.naix")

    add_custom_command(
        OUTPUT "${narc}" "${naix}"

        COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_encounter_archive_dir}"
        COMMAND "${CMAKE_COMMAND}" -E rm -rf "${stage}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${stage}"
        COMMAND $<TARGET_FILE:${emitter}> "${stage}" "${version}_enc_data"
        COMMAND $<TARGET_FILE:hg_nitroarc> -cf "${narc}" --index-namespace "${stage}"
        COMMAND "${Python3_EXECUTABLE}" "${hg_encounter_validator}"
            --json "${hg_encounter_json}"
            --species "${game_source}/include/constants/species.h"
            --encounter-header "${game_source}/include/encounter_tables_narc.h"
            --map-headers "${game_source}/src/data/map_headers.h"
            --variant "${variant}"
            --narc "${narc}" --naix "${naix}"
        DEPENDS
            ${emitter} hg_nitroarc "${hg_encounter_c}"
            "${hg_encounter_emitter}" "${hg_encounter_validator}"
            "${game_source}/include/wild_encounter.h"
            "${game_source}/include/constants/species.h"
            "${game_source}/include/constants/maps.h"
            "${game_source}/include/encounter_tables_narc.h"
            "${game_source}/src/data/map_headers.h"
        VERBATIM)
    list(APPEND hg_encounter_archives "${narc}" "${naix}")
endforeach()

add_custom_target(heartgold_encounter_assets ALL DEPENDS ${hg_encounter_archives})

# CTest invokes the validator again even when the archive hasn't rebuilt.
# (Building the archive target is a prerequisite to running this test.)
foreach(version IN ITEMS g s)
    if(version STREQUAL "g")
        set(variant ENC_HEARTGOLD)
    else()
        set(variant ENC_SOULSILVER)
    endif()
    add_test(NAME "encounters_${version}" COMMAND "${Python3_EXECUTABLE}"
        "${hg_encounter_validator}"
        --json "${hg_encounter_json}"
        --species "${game_source}/include/constants/species.h"
        --encounter-header "${game_source}/include/encounter_tables_narc.h"
        --map-headers "${game_source}/src/data/map_headers.h"
        --variant "${variant}"
        --narc "${hg_encounter_archive_dir}/${version}_enc_data.narc"
        --naix "${hg_encounter_archive_dir}/${version}_enc_data.naix")
endforeach()
