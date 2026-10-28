# Build the original HeartGold otherpoke archive from its conversion manifest.
set(hg_other_source "${game_source}/files/poketool/pokegra")
set(hg_other_manifest "${hg_other_source}/otherpoke.txt")
set(hg_other_build
    "${CMAKE_BINARY_DIR}/generated/files/poketool/pokegra/build-otherpoke")

set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${hg_other_manifest}")

file(STRINGS "${hg_other_manifest}" hg_other_lines)

set(hg_other_outputs)
foreach(instruction IN LISTS hg_other_lines)
    string(STRIP "${instruction}" instruction)
    if(instruction STREQUAL "" OR instruction MATCHES "^#")
        continue()
    endif()

    separate_arguments(parts UNIX_COMMAND "${instruction}")
    list(LENGTH parts count)
    if(count LESS 3)
        message(FATAL_ERROR "Invalid otherpoke instruction: ${instruction}")
    endif()

    list(GET parts 0 relative_input)
    list(GET parts 1 relative_output)
    list(REMOVE_AT parts 0 1)

    set(input "${game_source}/${relative_input}")
    set(output "${relative_output}")
    set(expected_prefix "files/poketool/pokegra/build-otherpoke/")

    string(FIND "${relative_output}" "${expected_prefix}" prefix_pos)
    if(NOT prefix_pos EQUAL 0)
        message(FATAL_ERROR "Unexpected otherpoke output: ${relative_output}")
    endif()

    string(REPLACE "${expected_prefix}" "${hg_other_build}/"
        output "${relative_output}")

    if(NOT EXISTS "${input}")
        message(FATAL_ERROR "Missing original sprite: ${input}")
    endif()

    set(inputs "${input}" "${hg_other_manifest}")
    if(EXISTS "${input}.key")
        list(APPEND inputs "${input}.key")
    endif()

    add_custom_command(
        OUTPUT "${output}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_other_build}"
        COMMAND $<TARGET_FILE:hg_nitrogfx>
            "${input}" "${output}" ${parts}
        DEPENDS hg_nitrogfx ${inputs}
        VERBATIM
    )

    list(APPEND hg_other_outputs "${output}")
endforeach()

list(LENGTH hg_other_outputs hg_other_count)
if(NOT hg_other_count EQUAL 261)
    message(FATAL_ERROR
        "Expected 261 original otherpoke conversions, found ${hg_other_count}")
endif()

hg_narc(heartgold_otherpoke_assets "poketool/pokegra/otherpoke"
    "${hg_other_build}" ${hg_other_outputs})
