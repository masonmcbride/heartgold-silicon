# Original message encoding rules from pinned pokeheartgold/msg.mk.
set(hg_msg_source "${game_source}/files/msgdata/msg")
set(hg_msg_dir "${PROJECT_BINARY_DIR}/generated/files/msgdata/msg")
set(hg_msg_mk "${game_source}/files/msgdata/msg.mk")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${hg_msg_mk}")

file(GLOB hg_gmms CONFIGURE_DEPENDS "${hg_msg_source}/*.gmm")

set(hg_trainer_gmm "${hg_msg_dir}/msg_0729.gmm")
add_custom_command(
    OUTPUT "${hg_trainer_gmm}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_msg_dir}"
    COMMAND $<TARGET_FILE:hg_jsonproc>
        "${game_source}/files/poketool/trainer/trainers.json"
        "${game_source}/files/poketool/trainer/trname.json.txt"
        "${hg_trainer_gmm}"
    COMMAND "${CMAKE_COMMAND}" "-DINPUT=${hg_trainer_gmm}"
        -P "${CMAKE_CURRENT_LIST_DIR}/escape_gmm.cmake"
    DEPENDS hg_jsonproc
        "${game_source}/files/poketool/trainer/trainers.json"
        "${game_source}/files/poketool/trainer/trname.json.txt"
        "${CMAKE_CURRENT_LIST_DIR}/escape_gmm.cmake"
    VERBATIM)

list(APPEND hg_gmms "${hg_trainer_gmm}")

# Sort by message filename, not absolute source path.
# The generated trainer message must occupy its original archive index.
set(hg_named_gmms)
foreach(gmm IN LISTS hg_gmms)
    get_filename_component(name "${gmm}" NAME)
    list(APPEND hg_named_gmms "${name}|${gmm}")
endforeach()
list(SORT hg_named_gmms)

set(hg_gmms)
foreach(entry IN LISTS hg_named_gmms)
    string(REGEX REPLACE "^[^|]*\\|" "" gmm "${entry}")
    list(APPEND hg_gmms "${gmm}")
endforeach()
file(READ "${hg_msg_mk}" hg_msg_rules)

set(hg_bins)
set(hg_archive_order "")
foreach(gmm IN LISTS hg_gmms)
    get_filename_component(stem "${gmm}" NAME_WE)
    set(bin "${hg_msg_dir}/${stem}.bin")
    set(header "${hg_msg_dir}/${stem}.h")

    string(REGEX MATCH
        "files/msgdata/msg/${stem}\\.bin: MSGENCFLAGS \\+= -k (0x[0-9A-Fa-f]+)"
        found "${hg_msg_rules}")

    set(key_args)
    if(found)
        list(APPEND key_args -k "${CMAKE_MATCH_1}")
    endif()

    add_custom_command(
        OUTPUT "${bin}" "${header}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_msg_dir}"
        COMMAND $<TARGET_FILE:hg_msgenc>
            -e -c "${game_source}/charmap.txt"
            --gmm -H "generated/files/msgdata/msg/${stem}.h" ${key_args}
            "${gmm}" "${bin}"
        DEPENDS hg_msgenc "${gmm}" "${game_source}/charmap.txt"
            "${hg_msg_mk}"
        # MSGENC derives a C guard from -H; keep this path relative and stable.
        WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
        VERBATIM)

    list(APPEND hg_bins "${bin}")
    string(APPEND hg_archive_order "${stem}.bin\n")
endforeach()

set(hg_order "${PROJECT_BINARY_DIR}/generated/message-order.txt")
file(GENERATE OUTPUT "${hg_order}" CONTENT "${hg_archive_order}")

set(hg_narc "${PROJECT_BINARY_DIR}/generated/files/msgdata/msg.narc")
set(hg_naix "${PROJECT_BINARY_DIR}/generated/files/msgdata/msg.naix")

add_custom_command(
    OUTPUT "${hg_narc}" "${hg_naix}"
    COMMAND $<TARGET_FILE:hg_nitroarc>
        -cf "${hg_narc}" --index-namespace
        -T "${hg_order}" -E "*"
        "${hg_msg_dir}"
    DEPENDS hg_nitroarc ${hg_bins} "${hg_order}"
    VERBATIM)

add_custom_target(heartgold_msg_assets DEPENDS "${hg_narc}" "${hg_naix}")

list(LENGTH hg_gmms hg_count)
message(STATUS "HeartGold: ${hg_count} message sources configured")
