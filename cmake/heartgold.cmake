# main.lsf owns ARM9 source/image membership. SDK code is supplied by libntr;
# overlays and ARM assembly are inventoried, never silently merged into main.
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${game_source}/main.lsf"
    "${game_source}/global.inc" "${game_source}/heartgold.us/main.sha1"
    "${game_source}/soulsilver.us/main.sha1")
set(hg_image_graph_script "${CMAKE_CURRENT_LIST_DIR}/native_image_graph.py")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${hg_image_graph_script}")
execute_process(COMMAND "${Python3_EXECUTABLE}" -B "${hg_image_graph_script}"
    --game "${game_source}" --out "${PROJECT_BINARY_DIR}/native-graph"
    COMMAND_ERROR_IS_FATAL ANY)
include("${PROJECT_BINARY_DIR}/native-graph/sources.cmake")

# One guarded transformation, one output per original input. Headers retain their
# original include names; sources retain their original relative path and #line.
set(native_root "${PROJECT_BINARY_DIR}/native")
set(native_script "${CMAKE_CURRENT_LIST_DIR}/native_sources.py")
function(native_generate kind input output)
    add_custom_command(OUTPUT "${output}"
        COMMAND "${Python3_EXECUTABLE}" -B "${native_script}"
            --root "${game_source}" --kind "${kind}"
            --input "${input}" --output "${output}"
        COMMAND "${CMAKE_COMMAND}" -E touch_nocreate "${output}"
        DEPENDS "${native_script}" "${PROJECT_SOURCE_DIR}/cmake/native_coordinated.py"
            "${PROJECT_SOURCE_DIR}/cmake/native_pristine_compat.json" "${input}" ${ARGN}
        VERBATIM)
endfunction()

execute_process(COMMAND "${Python3_EXECUTABLE}" -B "${native_script}" --list-main-sources
    OUTPUT_VARIABLE native_sources OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY)
foreach(relative IN LISTS native_sources)
    set(output "${native_root}/${relative}")
    list(FIND game_sources "${game_source}/${relative}" index)
    if(index EQUAL -1)
        message(FATAL_ERROR "Adapted source missing from main.lsf: ${relative}")
    endif()
    native_generate(native "${game_source}/${relative}" "${output}")
    list(REMOVE_AT game_sources ${index})
    list(APPEND game_sources "${output}")
endforeach()

set(native_headers
    lib/include/nnsys/g3d/kernel.h
    include/field/map_prop_render.h
    include/frontier/frontier_script_commands.h
    include/map_object_movement.h include/field_union_chat_marker.h include/map_object_movement_commands_internal.h include/render_model.h include/script.h include/field_ground_dust.h include/encounter.h include/player_avatar_actions.h include/player_avatar_movement.h include/field_footprints.h include/render_animation.h include/field_warp_reset.h include/field_trainer_reveal.h include/field_warp_arrow.h include/field_rock_climb_effect.h include/field_shadow.h include/field_follow_mon_ball.h include/follow_mon.h include/field_tall_grass.h include/field_very_tall_grass.h include/field_unused_billboard_effect.h include/field_reflection.h include/map_object_movement_utilities.h include/field_puddle_splash.h include/field_apricorn_regrowth.h include/union_room_objects.h include/field_hidden_object_cover.h include/field_mud_splash.h include/field_emote_bubble.h include/field_shallow_water_ripple.h include/comm_player_manager_internal.h include/field_system.h include/field/map_object_render_internal.h include/field/apricorn_tree_anim.h include/field/map_object_billboard_motion.h include/field/field_effect_helpers.h include/field/fly_landing_effect.h include/field/map_object_model_list.h include/field/field_move_cut_in.h include/field/field_flash_darkness.h include/field/map_object_render.h include/field/spin_slide.h include/field/map_object_models.h include/field/field_effect_manager_internal.h include/field/field_shaymin_form_change.h include/field_time_events.h include/overlay_01.h include/field_misc_events.h include/spin_trade_flow.h include/npc_trade.h include/get_egg.h include/field_terrain.h include/colosseum_internal.h include/mailbox_app.h include/comm_player_manager.h include/launch_application.h include/wireless_trade_select_mon_internal.h include/union_chat_log.h include/pokeathlon_course_task.h include/script_manager.h include/gymmick_init.h include/bug_contest.h include/magnet_train_ride.h include/save_local_field_data.h include/overlay_02.h include/mart.h include/alph_checks.h include/field_transition_effects.h include/field_move.h include/field_warp_reset_suppress.h include/map_object_manager.h include/spawn_warp_lookup_internal.h include/blackout.h include/map_object_behavior.h include/communication_club_link.h include/field_system_rtc_weather.h include/frontier_field_system.h include/scrcmd.h include/headbutt_tree.h include/overlay_26.h include/money_box.h include/terrain_attributes.h include/map_object_movement_commands.h include/legendary_cinematic_task.h include/overlay_03.h include/field_bgm.h include/frontier_field_support.h include/union_room_talk.h include/union_room_internal.h include/apricorn_tree.h include/union_room.h include/spawn_warp.h include/map_object_movement_utilities_internal.h include/ship_voyage.h include/catching_show.h include/overlay_124.h include/location_backup.h include/overlay_25.h include/vs_recorder_app_internal.h include/gymmick_collision.h include/choose_starter.h include/overlay_04.h include/field_interaction.h include/gear_phone_ring_manager.h include/trainer_card_data.h include/communication_club_link_internal.h include/field_take_photo.h include/global_terminal/global_terminal_app.h include/record_mixing/record_mixing.h include/field/pal_pad_registration.h include/field/encounter_check.h include/field/script_menu.h include/field/door_transition.h include/field/touch_mart_app.h include/field/rock_smash_item.h include/field/warp_spin.h include/field/field_camera_zoom.h include/field/map_load_manager.h include/field/field_control.h include/field/field_camera.h include/field/field_move_effects.h include/field/touchscreen_choice_menu.h include/field/field_bottom_screen.h include/field/signpost.h include/field/field_follow_mon.h include/field/encounter_effect.h include/field/legend_cutscene_camera.h include/field/bottom_screen_app.h include/field/fieldmap.h include/frontier/frontier.h include/application/view_photo.h include/overlay_2/overlay_02_field_utils.h include/overlay_2/event_cutscene.h include/overlay_2/gear_phone_calls.h src/data/fieldmap/script_cmd_table.h include/naming_screen.h include/task.h include/launch_application_internal.h include/party_menu.h include/safari_decoration_task.h include/map_events.h include/frontier_launch.h include/safari_zone_encounters.h include/trade_communication_internal.h include/global_terminal/global_terminal_app_internal.h include/record_mixing/record_mixing_internal.h include/field/overlay116_scene_internal.h include/field/encounter_effect_leaders.h include/field/map_load_manager_internal.h include/frontier/battle_arcade_setup.h include/frontier/battle_tower_setup.h include/frontier/battle_factory_setup.h include/frontier/battle_castle_setup.h include/frontier/battle_hall_setup.h include/application/mailbox_app_internal.h include/application/pokegear/pokegear_internal.h include/battle_transition_task.h include/battle_greeting_task.h include/drawing_session.h include/party_context_menu.h include/oaks_speech.h include/mart_bag_task.h include/game_clear.h include/overlay_94.h include/map_preview_graphic.h include/hatch_egg_task.h include/party_menu_list_items.h include/wifi_club.h include/field_overworld_transition.h include/oaks_speech_internal.h include/party_menu_sprites.h include/field_transition_tasks.h include/touch_save_app.h include/hatch_egg_task_data.h include/alph_puzzle.h include/field_warp_tasks.h include/party_menu_items.h include/field_overworld_restore.h include/start_menu.h include/scrcmd_link_sync.h include/field_use_item.h include/gts/gts_internal.h include/field/weather_manager.h include/application/palpad/palpad_internal.h include/application/apricorn_box/apricorn_box_overlay_internal.h include/application/pokegear/radio/radio_internal.h include/application/pokegear/configure/pokegear_configure_internal.h include/application/pokegear/map/pokegear_map_internal.h include/application/pokegear/phone/phone_internal.h include/hatch_egg_app_internal.h include/bag_view.h include/application/apricorn_box/apricorn_box_screen_internal.h
    include/field_effects.h include/field/field_effect_manager.h include/player_avatar.h include/field_surf_mount.h include/field_emote_mark.h include/map_object_behavior_internal.h include/map_object_follow_internal.h include/map_object_follow.h include/map_object.h
    include/lobby_chat_request.h include/lobby_chat_internal.h
    include/lobby_vector.h
    include/lobby_tree.h include/lobby_chat_manager.h include/ppw_lobby_work.h
    include/overlay45_string_search.h
    include/lobby_sort.h
    include/berry_pots_app_internal.h include/nintendo_wfc_connect_unused.h
    include/wifi_plaza/wifi_plaza_internal.h
    include/wifi_setup/wifi_setup_ui.h
    lib/include/dwc/http_internal.h lib/include/dwc/chat_internal.h
    include/comm_state_internal.h include/orbit_cursor.h include/field/field_fog.h
    include/drawing_session_link_internal.h include/record_mixing/record_mixing_link_internal.h
    include/voice_chat.h lib/include/nitro/os/printf.h lib/include/vct/vct_audio_internal.h
    lib/include/nitro/wm/wm_internal.h lib/include/nitro/os/ownerInfo.h
    lib/include/nnsys/g3d_render_internal.h lib/include/nnsys/snd_internal.h
    lib/include/nnsys/snd_arc_internal.h lib/include/nnsys/snd_arc_strm_internal.h
    lib/include/nnsys/g2d/g2d_CellTransferManager.h lib/NitroDWC/src/tree-iterator4.h)
list(APPEND native_headers
    lib/include/dwc/auth_internal.h
    lib/include/dwc/net_common_internal.h
    include/wifi_setup/wifi_setup_connection_screens.h
    include/application/pokewalker/pokewalker_ir.h
    include/application/pokewalker/pokewalker_ir_internal.h
    lib/include/nitro/card/card_spi_wait_internal.h)
set(header_outputs)
foreach(relative IN LISTS native_headers)
    set(extra)
    if(relative STREQUAL "include/application/pokewalker/pokewalker_ir_internal.h")
        list(APPEND extra "${game_source}/src/application/pokewalker/pokewalker_ir_requests.c")
    endif()
    set(output "${native_root}/${relative}")
    native_generate(native "${game_source}/${relative}" "${output}" ${extra})
    list(APPEND header_outputs "${output}")
endforeach()
add_custom_target(heartgold_native_headers DEPENDS ${header_outputs})

# Exercise the same approved heap-common storage/layout adaptation as the game.
# The allocator remains original; build the registered CTest executable normally.
set_property(TARGET test_heap PROPERTY SOURCES
    "${PROJECT_SOURCE_DIR}/tests/test_heap.c"
    "${native_root}/lib/NitroSystem/src/fnd_expheap.c"
    "${native_root}/lib/NitroSystem/src/fnd_heapcommon.c"
    "${game_source}/lib/NitroSystem/src/fnd_list.c")

# Native overlay identities are derived from the original ARM9 linker manifest.
# Preserve all IDs; never collapse SDK_PORT overlay references to zero.
set(hg_overlay_count 0)
set(hg_overlay_header_text
    "#ifndef HG_NATIVE_OVERLAY_IDS_H\n#define HG_NATIVE_OVERLAY_IDS_H\n#include <cw/function_target.h>\n#include <nitro/fs/file.h>\n#include <nitro/fs/overlay.h>\n#undef FS_OVERLAY_ID\n#define FS_OVERLAY_ID(name) HG_OVERLAY_ID_##name\n")

foreach(hg_name IN LISTS hg_overlay_names)
    if(hg_name MATCHES "^OVY_([0-9]+)$")
        if(NOT "${CMAKE_MATCH_1}" STREQUAL "${hg_overlay_count}")
            message(FATAL_ERROR "Original overlay ID mismatch: ${hg_name}")
        endif()
    endif()

    string(APPEND hg_overlay_header_text
        "#define HG_OVERLAY_ID_${hg_name} ${hg_overlay_count}\n")
    math(EXPR hg_overlay_count "${hg_overlay_count} + 1")
endforeach()

if(NOT hg_overlay_count EQUAL 129)
    message(FATAL_ERROR "Expected 129 original overlays, found ${hg_overlay_count}")
endif()

list(GET hg_overlay_names 36 hg_overlay_36)
list(GET hg_overlay_names 60 hg_overlay_60)
if(NOT hg_overlay_36 STREQUAL "OVY_36"
   OR NOT hg_overlay_60 STREQUAL "intro_title")
    message(FATAL_ERROR "Original boot overlay identities changed")
endif()

string(APPEND hg_overlay_header_text "#endif\n")
set(hg_native_overlay_header
    "${PROJECT_BINARY_DIR}/native/heartgold_overlay_ids.h")
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/native")
if(EXISTS "${hg_native_overlay_header}")
    file(READ "${hg_native_overlay_header}" hg_previous_header)
endif()
if(NOT "${hg_previous_header}" STREQUAL "${hg_overlay_header_text}")
    file(WRITE "${hg_native_overlay_header}" "${hg_overlay_header_text}")
endif()

set(msl_runtime)
foreach(relative IN ITEMS lib/MSL_C/src/msl_strtoul.c lib/MSL_C/src/msl_strtoul_core.c
        lib/MSL_C/src/msl_scanf_string_read.c lib/MSL_C/src/msl_qsort.c
        lib/MSL_C/asm/MSL_Common_ctype.s)
    string(REGEX REPLACE "\\.s$" ".c" native_relative "${relative}")
    set(output "${native_root}/${native_relative}")
    native_generate(coordinated-msl "${game_source}/${relative}" "${output}")
    list(APPEND msl_runtime "${output}")
endforeach()
set(native_hash1 "${native_root}/lib/NitroSDK/src/dgt_hash1.c")
add_custom_command(OUTPUT "${native_hash1}"
    COMMAND "${Python3_EXECUTABLE}" -B
        "${PROJECT_SOURCE_DIR}/cmake/native_hash1.py"
        --source "${game_source}/lib/NitroSDK/src/dgt_hash.c"
        --asm "${game_source}/lib/asm/nitro_sdk_data.s"
        --output "${native_hash1}"
    COMMAND "${CMAKE_COMMAND}" -E touch_nocreate "${native_hash1}"
    DEPENDS
        "${PROJECT_SOURCE_DIR}/cmake/native_hash1.py"
        "${game_source}/lib/NitroSDK/src/dgt_hash.c"
        "${game_source}/lib/asm/nitro_sdk_data.s"
    VERBATIM)
native_generate(native "${game_source}/lib/src/nitrocrypto_rc4_fast.c"
    "${native_root}/lib/src/nitrocrypto_rc4_fast.c")
add_library(heartgold_runtime STATIC ${msl_runtime}
    "${native_hash1}"
    "${game_source}/lib/NitroWiFi/src/stubsmd5.c"
    "${native_root}/lib/src/nitrocrypto_rc4_fast.c"
    "${game_source}/lib/src/nitrocrypto_rc4_init.c"
    "${game_source}/lib/MSL_C/src/msl_string_extras.c")
target_include_directories(heartgold_runtime PRIVATE "${game_source}/include/library")
add_executable(test_rc4_native "${PROJECT_SOURCE_DIR}/tests/test_rc4_native.c"
    "${native_root}/lib/src/nitrocrypto_rc4_fast.c"
    "${game_source}/lib/src/nitrocrypto_rc4_init.c")
target_include_directories(test_rc4_native PRIVATE "${game_source}/include/library")
target_link_libraries(test_rc4_native PRIVATE nitro_config)
target_compile_options(test_rc4_native PRIVATE -UNDEBUG -fsanitize=address,undefined -fno-sanitize-recover=all)
target_link_options(test_rc4_native PRIVATE -fsanitize=address,undefined)
add_test(NAME rc4_native COMMAND test_rc4_native)
add_test(NAME vs_recorder_data COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_vs_recorder_data.py")
set_tests_properties(vs_recorder_data PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME dwc_socket_storage COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_dwc_socket_storage.py")
set_tests_properties(dwc_socket_storage PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME main_menu_storage COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_main_menu_storage.py")
set_tests_properties(main_menu_storage PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME system_card_native COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_system_card_native.py")
set_tests_properties(system_card_native PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
target_compile_options(heartgold_runtime PRIVATE "-iquote${game_source}/include")
target_link_libraries(heartgold_runtime PUBLIC nitro_config PRIVATE ntr_dgt)
target_sources(heartgold_runtime PRIVATE "${PROJECT_SOURCE_DIR}/hardware_drivers/os/svc_crc16.c")
target_link_libraries(heartgold_runtime PRIVATE ntr_math)
add_executable(test_svc_crc16 "${PROJECT_SOURCE_DIR}/tests/test_svc_crc16.c"
    "${PROJECT_SOURCE_DIR}/hardware_drivers/os/svc_crc16.c"
    "${ntr_source}/libraries/math/src/crc.c")
target_link_libraries(test_svc_crc16 PRIVATE nitro_config)
target_compile_options(test_svc_crc16 PRIVATE -UNDEBUG -fsanitize=address,undefined -fno-sanitize-recover=all)
target_link_options(test_svc_crc16 PRIVATE -fsanitize=address,undefined)
add_test(NAME svc_crc16 COMMAND test_svc_crc16)
# Original resident MSL assertion and middleware version providers.
target_sources(heartgold_runtime PRIVATE
    "${game_source}/lib/MSL_C/src/msl_assert.c"
    "${PROJECT_SOURCE_DIR}/cmake/native_msl_assert_data.S"
    "${PROJECT_SOURCE_DIR}/cmake/native_middleware_version.S")

target_include_directories(heartgold_runtime PUBLIC "${PROJECT_SOURCE_DIR}/hardware_drivers/os")

# Overlay sources are prepared without merging overlay code into the main image.
execute_process(COMMAND "${Python3_EXECUTABLE}" -B "${native_script}" --list-overlay-sources
    OUTPUT_VARIABLE overlay_native_sources OUTPUT_STRIP_TRAILING_WHITESPACE
    COMMAND_ERROR_IS_FATAL ANY)
set(overlay_native_outputs)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${native_script}" "${PROJECT_SOURCE_DIR}/cmake/native_coordinated.py")
foreach(relative IN LISTS overlay_native_sources)
    set(output "${native_root}/${relative}")
    list(FIND native_sources "${relative}" native_source_index)
    if(native_source_index EQUAL -1)
        set(extra)
        if(relative STREQUAL "src/application/pokewalker/pokewalker_ir_requests.c")
            list(APPEND extra "${game_source}/include/application/pokewalker/pokewalker_ir_internal.h"
                "${game_source}/src/application/pokewalker/pokewalker_ir_requests.alias-map.json")
        endif()
        native_generate(native "${game_source}/${relative}" "${output}" ${extra})
    endif()
    get_filename_component(original_directory "${game_source}/${relative}" DIRECTORY)
    set_property(SOURCE "${output}" APPEND PROPERTY COMPILE_OPTIONS
        "-iquote${original_directory}")
    list(FIND game_sources "${game_source}/${relative}" index)
    if(NOT index EQUAL -1)
        list(REMOVE_AT game_sources ${index})
        list(APPEND game_sources "${output}")
    endif()
    list(APPEND overlay_native_outputs "${output}")
endforeach()
add_custom_target(heartgold_overlay_native_sources ALL DEPENDS ${overlay_native_outputs})
add_custom_target(heartgold_runtime_sources DEPENDS ${msl_runtime})
add_dependencies(heartgold_runtime heartgold_runtime_sources heartgold_overlay_native_sources)

add_executable(test_coordinated "${PROJECT_SOURCE_DIR}/tests/test_coordinated.c"
    "${PROJECT_SOURCE_DIR}/tests/test_coordinated_cpp.cpp"
    ${msl_runtime}
    "${ntr_source}/libraries/dgt/src/hash2.c"
    "${ntr_source}/libraries/os/src/os_alloc.c"
    "${ntr_source}/libraries/gx/src/g2.c"
    "${native_root}/lib/src/nitrocrypto_rc4.c"
    "${game_source}/lib/src/nitrocrypto_rc4_init.c")
target_include_directories(test_coordinated PRIVATE "${game_source}/include/library")
target_compile_options(test_coordinated PRIVATE "-iquote${native_root}/include" "-iquote${game_source}/include" "-idirafter${game_source}/lib/include")
target_link_libraries(test_coordinated PRIVATE nitro_sdk heartgold_runtime)
target_compile_options(test_coordinated PRIVATE -UNDEBUG -fsanitize=address,undefined -fno-sanitize-recover=all)
target_link_options(test_coordinated PRIVATE -fsanitize=address,undefined)
add_dependencies(test_coordinated fx_constants heartgold_native_headers heartgold_runtime_sources heartgold_overlay_native_sources)
add_test(NAME coordinated_native COMMAND test_coordinated)
add_test(NAME lobby_tree_native COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_lobby_tree_native.py"
    --root "${PROJECT_SOURCE_DIR}" --build "${PROJECT_BINARY_DIR}"
    --compiler "${CMAKE_CXX_COMPILER}")
add_test(NAME lobby_strings_native COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_lobby_strings_native.py"
    --root "${PROJECT_SOURCE_DIR}" --build "${PROJECT_BINARY_DIR}"
    --compiler "${CMAKE_CXX_COMPILER}")
add_test(NAME lobby_callbacks_native COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_lobby_callbacks_native.py"
    --root "${PROJECT_SOURCE_DIR}" --build "${PROJECT_BINARY_DIR}"
    --compiler "${CMAKE_CXX_COMPILER}")
add_test(NAME multiboot_native COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_mb_native.py"
    --root "${PROJECT_SOURCE_DIR}" --build "${PROJECT_BINARY_DIR}" --compiler "${CMAKE_C_COMPILER}")
add_test(NAME lobby_timers_native COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_lobby_timers_native.py"
    --root "${PROJECT_SOURCE_DIR}" --build "${PROJECT_BINARY_DIR}" --compiler "${CMAKE_CXX_COMPILER}")
add_test(NAME linker_provider_data COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_linker_provider_data.py"
    --game "${game_source}" --build "${PROJECT_BINARY_DIR}" --compiler "${CMAKE_C_COMPILER}")
add_test(NAME native_source_pipeline COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/cmake/native_sources.py"
    --audit --root "${game_source}" --output "${PROJECT_BINARY_DIR}/native-source-audit.json")
add_test(NAME coordinated_sources COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_coordinated_sources.py")

add_library(heartgold_main STATIC ${game_sources})
# Resident Wi-Fi storage; original cartridge state is owned by OVY_74.
target_sources(heartgold_main PRIVATE
    "${PROJECT_SOURCE_DIR}/cmake/native_gba_wifi_typed_state.s")

include("${CMAKE_CURRENT_LIST_DIR}/wifi_constants.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/wifi_bss_safe.cmake")
# Native implementation of the original main-owned VCT packet allocator.
# The generated C retains the original free-list algorithm with ARM64 slot geometry.
# Fail closed if the original or adapted member has already entered game_sources.
list(FIND game_sources
    "${game_source}/lib/libVCT/src/vct_packet_buffer.c" hg_vct_original_index)
list(FIND game_sources
    "${native_root}/lib/libVCT/src/vct_packet_buffer.c" hg_vct_native_index)
if(NOT hg_vct_original_index EQUAL -1 OR NOT hg_vct_native_index EQUAL -1)
    message(FATAL_ERROR "VCT packet allocator already owned by heartgold_main")
endif()
target_sources(heartgold_main PRIVATE
    "${native_root}/lib/libVCT/src/vct_packet_buffer.c")
# Permanent native storage for the two original main-owned VCT BSS members.
# ARM64 structure widths require expanded storage and preserved SSP aliases.
# The Nintendo assembly sources remain unchanged.
target_sources(heartgold_main PRIVATE
    "${PROJECT_SOURCE_DIR}/hardware_drivers/audio/vct_native_bss.S")


# HG_VCT_COMPLETE_NATIVE_C
# Original main-owned VCT C members.
# The packet allocator is registered separately.
# Audio send uses the existing native-source generation rule.
set(hg_vct_other_members
    "lib/libVCT/src/vct_adpcm.c"
    "lib/libVCT/src/vct_audio.c"
    "lib/libVCT/src/vct_audio_queue.c"
    "lib/libVCT/src/vct_audio_send.c"
    "lib/libVCT/src/vct_codec.c"
    "lib/libVCT/src/vct_decoder.c"
    "lib/libVCT/src/vct_fir.c"
    "lib/libVCT/src/vct_main.c"
    "lib/libVCT/src/vct_mix.c"
    "lib/libVCT/src/vct_ssp.c"
    "lib/libVCT/src/vct_vad.c"
)
foreach(hg_vct_member IN LISTS hg_vct_other_members)
    list(FIND game_sources "${game_source}/${hg_vct_member}" hg_vct_original)
    list(FIND game_sources "${native_root}/${hg_vct_member}" hg_vct_native)
    if(NOT hg_vct_original EQUAL -1 OR NOT hg_vct_native EQUAL -1)
        message(FATAL_ERROR "Duplicate main VCT member: ${hg_vct_member}")
    endif()
    if(hg_vct_member STREQUAL "lib/libVCT/src/vct_audio_send.c" OR hg_vct_member STREQUAL "lib/libVCT/src/vct_audio.c" OR hg_vct_member STREQUAL "lib/libVCT/src/vct_fir.c" OR hg_vct_member STREQUAL "lib/libVCT/src/vct_vad.c")
        target_sources(heartgold_main PRIVATE "${native_root}/${hg_vct_member}")
    else()
        target_sources(heartgold_main PRIVATE "${game_source}/${hg_vct_member}")
    endif()
endforeach()

# Native storage for the original main-owned SPL members selected by the graph.
target_sources(heartgold_main PRIVATE
    "${PROJECT_SOURCE_DIR}/hardware_drivers/graphics/native_spl_data.c")

# The SDK_PORT MI manifest has no native MIi_CpuClearFast definition. Translate
# only the original game's ARM routine; never substitute byte-pattern memset.
set(native_mi_clear "${native_root}/lib/NitroSDK/src/mi/mi_clear_fast.c")
native_generate(native-mi-clear-fast
    "${game_source}/lib/NitroSDK/src/mi/mi_memory.c" "${native_mi_clear}")
target_sources(heartgold_runtime PRIVATE "${native_mi_clear}"
    "${PROJECT_SOURCE_DIR}/hardware_drivers/os/msl_arithmetic.c"
    "${PROJECT_SOURCE_DIR}/hardware_drivers/os/card_spi_host.c")
set(msl_fp_original "${game_source}/lib/MSL_C/src/msl_fp_runtime.c")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${msl_fp_original}")
file(SHA256 "${msl_fp_original}" msl_fp_digest)
if(NOT msl_fp_digest STREQUAL "4772579d74e6406a595ce01ebbbcc45b1f64bf7b7b79833b16b509f591c1dcaa")
    message(FATAL_ERROR "Original MSL arithmetic runtime changed; revalidate native ABI bridges")
endif()
add_test(NAME native_msl_arithmetic COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_msl_arithmetic.py"
    --build "${PROJECT_BINARY_DIR}" --compiler "${CMAKE_C_COMPILER}")
add_test(NAME pokewalker_native_abi COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_pokewalker_native.py"
    --build "${PROJECT_BINARY_DIR}" --compiler "${CMAKE_C_COMPILER}")
# Original CARD protocol, with native pointer storage and an explicit physical
# cartridge register boundary. No successful hardware response is synthesized.
foreach(member card_spi_wait card_spi_wait_cycles card_spi_wait_init)
    set(output "${native_root}/lib/NitroSDK/src/card/${member}.c")
    native_generate(native "${game_source}/lib/NitroSDK/src/card/${member}.c" "${output}")
    target_sources(heartgold_runtime PRIVATE "${output}")
endforeach()
set(card_storage "${native_root}/lib/asm/card_spi_storage.c")
native_generate(native-card-spi-storage "${game_source}/lib/asm/nitro_sdk_data.s" "${card_storage}")
target_sources(heartgold_runtime PRIVATE "${card_storage}")
target_include_directories(heartgold_runtime BEFORE PRIVATE "${native_root}/lib/include")
add_dependencies(heartgold_runtime heartgold_native_headers)
# main.lsf:677 assigns the complete original WM request member to resident.
# Audit the complete member without admitting widened ARM7 wire records into
# the resident link. A guest32 WM boundary is required before admission.
set(native_wm_requests "${native_root}/lib/NitroSDK/src/wm_requests.c")
# The coordinated source list above already declares its single output.
add_library(heartgold_wm_requests_audit OBJECT EXCLUDE_FROM_ALL "${native_wm_requests}")
target_compile_definitions(heartgold_wm_requests_audit PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
target_include_directories(heartgold_wm_requests_audit PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_options(heartgold_wm_requests_audit PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>")
target_link_libraries(heartgold_wm_requests_audit PRIVATE nitro_config)
add_dependencies(heartgold_wm_requests_audit
    heartgold_overlay_native_sources heartgold_native_headers fx_constants)
add_test(NAME linker_contracts COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_linker_contracts.py"
    --root "${PROJECT_SOURCE_DIR}" --build "${PROJECT_BINARY_DIR}"
    --compiler "${CMAKE_C_COMPILER}")
target_link_libraries(heartgold_main PUBLIC heartgold_runtime)
target_link_libraries(heartgold_main PRIVATE nitro_sdk)

# Original ARM9 overlay 60 (intro_title).
# Compile original sources separately; native loading is implemented later.
add_library(heartgold_intro_title STATIC ${hg_original_image_intro_title_sources})

# Reuse the original main-image compiler environment at generation time.
# Empty properties expand to empty lists rather than NOTFOUND paths.
target_compile_definitions(heartgold_intro_title PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
target_include_directories(heartgold_intro_title PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_options(heartgold_intro_title PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>")
target_link_libraries(heartgold_intro_title PRIVATE nitro_sdk)

add_dependencies(heartgold_intro_title
    heartgold_native_headers
    fx_constants
)

target_compile_options(heartgold_main PRIVATE "$<$<COMPILE_LANGUAGE:C,CXX>:-include${hg_native_overlay_header}>")
target_compile_definitions(heartgold_main PRIVATE HEARTGOLD ENGLISH
    HG_GAME_REVISION="${HEARTGOLD_COMMIT}" HG_USE_ORIGINAL_WM
    OS_IE_VBLANK=OS_IE_V_BLANK OS_IE_HBLANK=OS_IE_H_BLANK)
target_include_directories(heartgold_main PRIVATE
    "${PROJECT_SOURCE_DIR}/hardware_drivers"
    "${PROJECT_SOURCE_DIR}/hardware_drivers/os"
    "${native_root}/include" "${native_root}/lib/include" "${native_root}/src"
    "${game_source}/src" "${game_source}/include" "${game_source}/include/library"
    "${game_source}/files" "${PROJECT_BINARY_DIR}/generated/files")
target_compile_options(heartgold_main PRIVATE
    "-idirafter${game_source}/lib/include"
    "-idirafter${game_source}/lib/NitroSDK/include")
add_dependencies(heartgold_main fx_constants heartgold_native_headers)
foreach(source src/field_transition_tasks.c src/wifi_plaza/wifi_plaza_player_info.c)
    set_property(SOURCE "${game_source}/${source}" APPEND PROPERTY COMPILE_OPTIONS
        -include "${native_root}/lib/NitroDWC/src/tree-iterator4.h")
endforeach()
set_property(SOURCE "${game_source}/src/colosseum.c" APPEND PROPERTY COMPILE_OPTIONS
    -include "${game_source}/lib/include/cw/function_target.h")

include("${CMAKE_CURRENT_LIST_DIR}/assets.cmake")
add_test(NAME resident_wifi_constants COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_wifi_constants.py"
    --game "${game_source}" --build "${PROJECT_BINARY_DIR}"
    --object "$<TARGET_OBJECTS:heartgold_wifi_constants>"
    --compiler "${CMAKE_C_COMPILER}" --objcopy "${HG_ASSET_OBJCOPY}"
    --readelf "${HG_ASSET_READELF}")
add_dependencies(heartgold_main ${heartgold_asset_targets})
add_dependencies(heartgold_intro_title ${heartgold_asset_targets})
add_executable(heartgold "${PROJECT_SOURCE_DIR}/tests/start_game.c")
target_link_libraries(heartgold PRIVATE heartgold_main nitro_sdk)
if(HEARTGOLD_LIBNTR_REVIEW_SOURCE)
    add_executable(test_resource_files "${PROJECT_SOURCE_DIR}/tests/test_resource_files.c")
    target_link_libraries(test_resource_files PRIVATE nitro_sdk)
    target_compile_options(test_resource_files PRIVATE -UNDEBUG)
    add_dependencies(test_resource_files ${heartgold_asset_targets})
    add_test(NAME native_resource_files COMMAND test_resource_files)
    add_executable(test_overlay_fs "${PROJECT_SOURCE_DIR}/tests/test_overlay_fs.c")
    target_include_directories(test_overlay_fs PRIVATE "${ntr_source}/libraries/fs/include")
    target_link_libraries(test_overlay_fs PRIVATE nitro_sdk)
    target_compile_options(test_overlay_fs PRIVATE -UNDEBUG -fsanitize=address,undefined -fno-sanitize-recover=all)
    target_link_options(test_overlay_fs PRIVATE -fsanitize=address,undefined)
    add_test(NAME native_overlay_lifecycle COMMAND "${Python3_EXECUTABLE}" -B
        "${PROJECT_SOURCE_DIR}/tests/test_overlay_native.py"
        --build "${PROJECT_BINARY_DIR}" --sdk "${ntr_source}"
        --compiler "${CMAKE_C_COMPILER}" --fs-test $<TARGET_FILE:test_overlay_fs>)
endif()
add_test(NAME script_conversion COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_scripts.py" --work "${PROJECT_BINARY_DIR}")
add_test(NAME native_adaptations COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_sources.py" --work "${PROJECT_BINARY_DIR}")
add_executable(test_sound "${PROJECT_SOURCE_DIR}/tests/test_sound.c"
    "${native_root}/lib/NitroSystem/src/snd_arc.c")
target_link_libraries(test_sound PRIVATE nitro_sdk)
target_include_directories(test_sound PRIVATE "${native_root}/lib/include")
target_compile_options(test_sound PRIVATE
    "-idirafter${game_source}/lib/include"
    -fsanitize=address,undefined -fno-sanitize-recover=all)
target_link_options(test_sound PRIVATE -fsanitize=address,undefined)
add_dependencies(test_sound heartgold_native_headers)
add_test(NAME sound_data COMMAND test_sound)
set_tests_properties(sound_data PROPERTIES ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0")

# Typed native storage for the sound labels owned by the original main image.
set(sound_storage_sources)
foreach(object nnsys_g3d_snd_bss nnsys_snd_arc_strm_bss nnsys_g2d_bss)
    set(output "${native_root}/lib/asm/${object}.c")
    native_generate(native-storage "${game_source}/lib/asm/${object}.s" "${output}"
        "${game_source}/lib/include/nnsys/snd_internal.h"
        "${game_source}/lib/include/nnsys/snd_arc_internal.h"
        "${game_source}/lib/include/nnsys/snd_arc_strm_internal.h"
        "${game_source}/lib/include/nnsys/g2d_internal.h"
        "${game_source}/lib/include/nnsys/g2d_renderer_internal.h"
        "${game_source}/lib/include/nnsys/g3d_render_internal.h"
        "${game_source}/lib/include/nnsys/g3d_util_internal.h"
        "${game_source}/lib/include/nnsys/g3d_anm_mat_internal.h"
        "${game_source}/main.lsf")
    list(APPEND sound_storage_sources "${output}")
endforeach()
add_library(heartgold_sound_storage STATIC ${sound_storage_sources})
target_link_libraries(heartgold_sound_storage PRIVATE nitro_sdk)
# Original nitro_link_order.json places the empty alias_d750 section immediately
# before SND_util's snd_decibel section: both names identify the same s16[128].
# Use the already emitted SDK table, preserving one owner and identical addresses.
target_link_options(heartgold_sound_storage INTERFACE
    "LINKER:-alias,_SNDi_DecibelTable,__0210D750")
target_include_directories(heartgold_sound_storage PRIVATE "${native_root}/lib/include")
target_compile_options(heartgold_sound_storage PRIVATE "-idirafter${game_source}/lib/include")
add_dependencies(heartgold_sound_storage heartgold_native_headers fx_constants)
target_link_libraries(heartgold_main PUBLIC heartgold_sound_storage)
add_executable(test_sound_storage "${PROJECT_SOURCE_DIR}/tests/test_sound_storage.c")
target_link_libraries(test_sound_storage PRIVATE heartgold_sound_storage nitro_sdk)
target_include_directories(test_sound_storage PRIVATE "${native_root}/lib/include")
target_compile_options(test_sound_storage PRIVATE "-idirafter${game_source}/lib/include" -O2)
add_dependencies(test_sound_storage heartgold_native_headers)
add_test(NAME sound_storage COMMAND test_sound_storage)


# HG_WM_39_PRODUCTION_ADMISSION
# Preserve original source bodies; no synthetic WM/WVR implementations.
foreach(_wm_member wm_core wm_settings wvr)
    set(_wm_source "${native_root}/lib/NitroSDK/src/${_wm_member}.c")
    if(EXISTS "${_wm_source}")
        target_sources(heartgold_main PRIVATE "${_wm_source}")
        message(STATUS "HG WM production source: ${_wm_source}")
    endif()
endforeach()
