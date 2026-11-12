# Original host tools and asset recipes. All generated data stays in build/.
find_program(HG_ASSET_OBJCOPY NAMES llvm-objcopy)
find_program(HG_ASSET_READELF NAMES llvm-readelf)
if(NOT HG_ASSET_OBJCOPY OR NOT HG_ASSET_READELF)
    # Keg-only LLVM need not be on PATH. Query its installed prefix, never assume it.
    find_program(HOMEBREW_EXECUTABLE NAMES brew)
    if(HOMEBREW_EXECUTABLE)
        execute_process(COMMAND "${HOMEBREW_EXECUTABLE}" --prefix llvm
            OUTPUT_VARIABLE llvm_prefix OUTPUT_STRIP_TRAILING_WHITESPACE
            RESULT_VARIABLE failed ERROR_QUIET)
        if(NOT failed)
            find_program(HG_ASSET_OBJCOPY NAMES llvm-objcopy HINTS "${llvm_prefix}/bin")
            find_program(HG_ASSET_READELF NAMES llvm-readelf HINTS "${llvm_prefix}/bin")
        endif()
    endif()
    if(NOT HG_ASSET_OBJCOPY OR NOT HG_ASSET_READELF)
        message(FATAL_ERROR "Game assets require llvm-objcopy and llvm-readelf. Install LLVM and expose its bin directory through PATH or CMAKE_PROGRAM_PATH.")
    endif()
endif()
find_package(PNG REQUIRED)
find_package(ZLIB REQUIRED)
set(hg_tools "${game_source}/tools")

file(GLOB nitroarc_sources CONFIGURE_DEPENDS "${hg_tools}/nitroarc/src/*.c")
add_executable(hg_nitroarc "${hg_tools}/nitroarc/lib/nitroarc.c" ${nitroarc_sources})
target_include_directories(hg_nitroarc PRIVATE "${hg_tools}/nitroarc/lib/include")
set_target_properties(hg_nitroarc PROPERTIES OUTPUT_NAME nitroarc)
add_executable(hg_msgenc
    "${hg_tools}/msgenc/msgenc.cpp" "${hg_tools}/msgenc/Options.cpp"
    "${hg_tools}/msgenc/MessagesConverter.cpp" "${hg_tools}/msgenc/MessagesDecoder.cpp"
    "${hg_tools}/msgenc/MessagesEncoder.cpp" "${hg_tools}/msgenc/Gmm.cpp"
    "${hg_tools}/msgenc/pugixml.cpp")
target_compile_features(hg_msgenc PRIVATE cxx_std_17)
target_compile_definitions(hg_msgenc PRIVATE NDEBUG) # Original Makefile default.
set_target_properties(hg_msgenc PROPERTIES OUTPUT_NAME msgenc)
add_executable(hg_jsonproc "${hg_tools}/jsonproc/jsonproc.cpp")
target_compile_features(hg_jsonproc PRIVATE cxx_std_11)
target_include_directories(hg_jsonproc PRIVATE "${hg_tools}/jsonproc")
set_target_properties(hg_jsonproc PROPERTIES OUTPUT_NAME jsonproc)
set(gfx "${hg_tools}/nitrogfx")
add_executable(hg_nitrogfx
    "${gfx}/main.c" "${gfx}/convert_png.c" "${gfx}/gfx.c" "${gfx}/jasc_pal.c"
    "${gfx}/lz.c" "${gfx}/rl.c" "${gfx}/util.c" "${gfx}/font.c"
    "${gfx}/huff.c" "${gfx}/json.c" "${gfx}/cJSON.c")
target_compile_features(hg_nitrogfx PRIVATE c_std_17)
target_compile_definitions(hg_nitrogfx PRIVATE PNG_SKIP_SETJMP_CHECK)
target_link_libraries(hg_nitrogfx PRIVATE PNG::PNG ZLIB::ZLIB)
set_target_properties(hg_nitrogfx PROPERTIES OUTPUT_NAME nitrogfx)

set(elf_reader "${PROJECT_BINARY_DIR}/native-tools/o2narc/RelocElfReader.cpp")
native_generate(o2narc-reader "${hg_tools}/o2narc/RelocElfReader.cpp" "${elf_reader}")
add_executable(hg_o2narc
    "${hg_tools}/o2narc/o2narc.cpp" "${hg_tools}/o2narc/Options.cpp" "${elf_reader}")
target_compile_features(hg_o2narc PRIVATE cxx_std_17)
target_include_directories(hg_o2narc PRIVATE "${hg_tools}/o2narc")
set_target_properties(hg_o2narc PROPERTIES OUTPUT_NAME o2narc)

# A NARC always has explicit member inputs and original ordering/exclusions.
function(hg_narc target relative directory)
    if(NOT ARGN)
        message(FATAL_ERROR "Empty original archive recipe: ${relative}")
    endif()
    set(original "${game_source}/files/${relative}")
    set(metadata)
    foreach(name .narcorder .narcignore)
        if(EXISTS "${original}/${name}")
            if(NOT "${directory}" STREQUAL "${original}")
                configure_file("${original}/${name}" "${directory}/${name}" COPYONLY)
            endif()
            list(APPEND metadata "${directory}/${name}")
        endif()
    endforeach()
    set(archive "${PROJECT_BINARY_DIR}/generated/files/${relative}.narc")
    set(index "${PROJECT_BINARY_DIR}/generated/files/${relative}.naix")
    get_filename_component(parent "${archive}" DIRECTORY)
    add_custom_command(OUTPUT "${archive}" "${index}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${parent}"
        COMMAND $<TARGET_FILE:hg_nitroarc> -cf "${archive}" --index-namespace "${directory}"
        DEPENDS hg_nitroarc ${ARGN} ${metadata}
        VERBATIM)
    add_custom_target(${target} DEPENDS "${archive}" "${index}")
endfunction()

set(matrix "${game_source}/files/fielddata/mapmatrix/map_matrix")
file(GLOB matrix_members CONFIGURE_DEPENDS "${matrix}/map_matrix_*.bin")
hg_narc(heartgold_mapmatrix_assets "fielddata/mapmatrix/map_matrix" "${matrix}" ${matrix_members})
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_messages.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_otherpoke.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_graphics.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_ppark.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_zone_event.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_scripts.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_encounters.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_item_data.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_mushi.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_json_binaries.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_resdat.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_zukan_data.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/heartgold_manifest_graphics.cmake")
# The original sound manifest identifies an existing SDAT; it is not generated
# from playback code or dependent on the historical DS linker.
set(sound_manifest "${game_source}/files/data/sound/sound_data.mk")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${sound_manifest}")
file(STRINGS "${sound_manifest}" sound_declaration REGEX "^SDAT := files/[^ ]+\\.sdat$")
if(NOT sound_declaration)
    message(FATAL_ERROR "Original sound archive manifest changed")
endif()
string(REGEX REPLACE "^SDAT := files/" "" sound_relative "${sound_declaration}")
set(sound_output "${PROJECT_BINARY_DIR}/generated/files/${sound_relative}")
get_filename_component(sound_parent "${sound_output}" DIRECTORY)
add_custom_command(OUTPUT "${sound_output}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${sound_parent}"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${game_source}/files/${sound_relative}" "${sound_output}"
    COMMAND "${CMAKE_COMMAND}" -E touch_nocreate "${sound_output}"
    DEPENDS "${game_source}/files/${sound_relative}" "${sound_manifest}"
    VERBATIM)
add_custom_target(heartgold_sound_archive_assets DEPENDS "${sound_output}")
set(heartgold_asset_targets
    heartgold_sound_archive_assets
    heartgold_mapmatrix_assets heartgold_msg_assets heartgold_otherpoke_assets
    heartgold_sbox_assets heartgold_camera_assets heartgold_preview_assets
    heartgold_record_assets heartgold_plist_assets heartgold_item_icon_assets
    heartgold_namein_assets heartgold_ppark_assets heartgold_zone_event_assets
    heartgold_script_assets heartgold_encounter_assets heartgold_item_data_assets
    heartgold_resdat_assets heartgold_zukan_data_assets
    heartgold_gs_opening_assets heartgold_titledemo_assets
    heartgold_zukan_enc_assets ${heartgold_overlay_index_targets})
add_custom_target(heartgold_overlay_index_assets
    DEPENDS heartgold_zukan_enc_assets ${heartgold_overlay_index_targets})
add_custom_target(assets DEPENDS ${heartgold_asset_targets})
add_test(NAME elf_reader COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_elf_reader.py"
    --tool $<TARGET_FILE:hg_o2narc> --work "${PROJECT_BINARY_DIR}")
add_test(NAME asset_indices COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_asset_indices.py"
    --build "${PROJECT_BINARY_DIR}" --tool $<TARGET_FILE:hg_nitroarc>)
set_tests_properties(asset_indices PROPERTIES TIMEOUT 300)
