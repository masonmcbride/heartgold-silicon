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
add_executable(hg_nitroarc_index "${CMAKE_CURRENT_LIST_DIR}/assets/nitroarc_index.c"
    "${hg_tools}/nitroarc/src/common.c" "${hg_tools}/nitroarc/lib/nitroarc.c")
target_include_directories(hg_nitroarc_index PRIVATE "${hg_tools}"
    "${hg_tools}/nitroarc/lib/include")
set_target_properties(hg_nitroarc_index PROPERTIES OUTPUT_NAME nitroarc-index)
add_library(hg_msgenc_core OBJECT
    "${hg_tools}/msgenc/Options.cpp" "${hg_tools}/msgenc/MessagesConverter.cpp"
    "${hg_tools}/msgenc/MessagesDecoder.cpp" "${hg_tools}/msgenc/MessagesEncoder.cpp"
    "${hg_tools}/msgenc/Gmm.cpp" "${hg_tools}/msgenc/pugixml.cpp")
target_compile_features(hg_msgenc_core PRIVATE cxx_std_17)
target_compile_options(hg_msgenc_core PRIVATE -O2)
target_compile_definitions(hg_msgenc_core PRIVATE NDEBUG)
add_executable(hg_msgenc "${hg_tools}/msgenc/msgenc.cpp" $<TARGET_OBJECTS:hg_msgenc_core>)
target_compile_features(hg_msgenc PRIVATE cxx_std_17)
target_compile_definitions(hg_msgenc PRIVATE NDEBUG)
set_target_properties(hg_msgenc PROPERTIES OUTPUT_NAME msgenc)
add_executable(hg_jsonproc "${hg_tools}/jsonproc/jsonproc.cpp")
target_compile_features(hg_jsonproc PRIVATE cxx_std_11)
target_include_directories(hg_jsonproc PRIVATE "${hg_tools}/jsonproc")
set_target_properties(hg_jsonproc PROPERTIES OUTPUT_NAME jsonproc)
set(gfx "${hg_tools}/nitrogfx")
add_library(hg_nitrogfx_core OBJECT
    "${gfx}/main.c" "${gfx}/convert_png.c" "${gfx}/gfx.c" "${gfx}/jasc_pal.c"
    "${gfx}/lz.c" "${gfx}/rl.c" "${gfx}/util.c" "${gfx}/font.c"
    "${gfx}/huff.c" "${gfx}/json.c" "${gfx}/cJSON.c")
target_compile_features(hg_nitrogfx_core PRIVATE c_std_17)
target_compile_definitions(hg_nitrogfx_core PRIVATE PNG_SKIP_SETJMP_CHECK main=hg_nitrogfx_entry)
target_compile_options(hg_nitrogfx_core PRIVATE -O2)
target_link_libraries(hg_nitrogfx_core PRIVATE PNG::PNG ZLIB::ZLIB)
add_executable(hg_nitrogfx "${PROJECT_SOURCE_DIR}/compiler/assets/gfx_entry.c" $<TARGET_OBJECTS:hg_nitrogfx_core>)
target_link_libraries(hg_nitrogfx PRIVATE PNG::PNG ZLIB::ZLIB)
set_target_properties(hg_nitrogfx PROPERTIES OUTPUT_NAME nitrogfx)
add_executable(hg_asset_compiler "${PROJECT_SOURCE_DIR}/compiler/assets/compiler.cpp"
    "${PROJECT_SOURCE_DIR}/compiler/assets/host.cpp" $<TARGET_OBJECTS:hg_nitrogfx_core>
    $<TARGET_OBJECTS:hg_msgenc_core>)
target_compile_features(hg_asset_compiler PRIVATE cxx_std_17)
target_compile_options(hg_asset_compiler PRIVATE -O2)
target_compile_definitions(hg_asset_compiler PRIVATE NDEBUG)
target_include_directories(hg_asset_compiler PRIVATE "${hg_tools}/jsonproc" "${hg_tools}/msgenc")
target_link_libraries(hg_asset_compiler PRIVATE PNG::PNG ZLIB::ZLIB)
include("${CMAKE_CURRENT_LIST_DIR}/assets/asset_batches.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/assets/native_assets.cmake")

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
    set_property(GLOBAL APPEND PROPERTY HG_ASSET_ARCHIVE_TARGETS "${target}")
endfunction()

# Script/event indices depend on original member names, not payload bytes.
# Both phases use one declared order and Nintendo's existing tool algorithms.
function(hg_ordered_archive target relative directory)
    if(NOT ARGN)
        message(FATAL_ERROR "Empty original archive recipe: ${relative}")
    endif()
    set(order "${PROJECT_BINARY_DIR}/generated/${target}-order.txt")
    set(contents "")
    foreach(member IN LISTS ARGN)
        get_filename_component(name "${member}" NAME)
        string(APPEND contents "${name}\n")
    endforeach()
    file(GENERATE OUTPUT "${order}" CONTENT "${contents}")
    set(archive "${PROJECT_BINARY_DIR}/generated/files/${relative}.narc")
    set(index "${PROJECT_BINARY_DIR}/generated/files/${relative}.naix")
    get_filename_component(parent "${archive}" DIRECTORY)
    add_custom_command(OUTPUT "${index}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${parent}"
        COMMAND $<TARGET_FILE:hg_nitroarc_index> "${archive}" "${order}"
        DEPENDS hg_nitroarc_index "${order}" VERBATIM)
    add_custom_target(${target}_index DEPENDS "${index}")
    add_custom_command(OUTPUT "${archive}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${parent}"
        COMMAND $<TARGET_FILE:hg_nitroarc> -cf "${archive}" -T "${order}" -E "*" "${directory}"
        DEPENDS hg_nitroarc "${order}" ${ARGN} VERBATIM)
    add_custom_target(${target} DEPENDS "${archive}")
    add_dependencies(${target} ${target}_index)
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
hg_asset_host_job(graphics copy "${game_source}/files/${sound_relative};${sound_manifest}" "${sound_output}")
add_custom_target(heartgold_sound_archive_assets DEPENDS "${sound_output}")
list(APPEND heartgold_asset_targets
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
set(heartgold_compile_asset_targets ${heartgold_asset_targets})
list(REMOVE_ITEM heartgold_compile_asset_targets heartgold_script_assets
    heartgold_zone_event_assets heartgold_sound_archive_assets)
list(APPEND heartgold_compile_asset_targets heartgold_scr_seq_assets_index
    heartgold_move_script_assets_index heartgold_subscript_assets_index
    heartgold_zone_event_assets_index)

# Recover the proven native CARD image from original resource names and the
# declared asset outputs. No checkpoint manifest or compiled input participates.
set(hg_cartridge_script "${PROJECT_SOURCE_DIR}/cmake/source_cartridge.py")
set(hg_cartridge "${PROJECT_BINARY_DIR}/cartridge/heartgold-source-cartridge.nds")
set(hg_cartridge_manifest "${PROJECT_BINARY_DIR}/cartridge/cartridge-manifest.json")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${hg_cartridge_script}" "${game_source}/filesystem.mk")
execute_process(COMMAND "${Python3_EXECUTABLE}" -B "${hg_cartridge_script}"
    --game "${game_source}" --generated "${PROJECT_BINARY_DIR}/generated/files"
    --output "${hg_cartridge}" --manifest "${hg_cartridge_manifest}" --plan
    OUTPUT_VARIABLE hg_cartridge_plan COMMAND_ERROR_IS_FATAL ANY)
string(JSON hg_cartridge_count LENGTH "${hg_cartridge_plan}")
math(EXPR hg_cartridge_last "${hg_cartridge_count} - 1")
set(hg_cartridge_inputs)
foreach(i RANGE ${hg_cartridge_last})
    string(JSON input GET "${hg_cartridge_plan}" ${i} source)
    list(APPEND hg_cartridge_inputs "${input}")
endforeach()
add_custom_command(OUTPUT "${hg_cartridge}" "${hg_cartridge_manifest}"
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_cartridge_script}"
        --game "${game_source}" --generated "${PROJECT_BINARY_DIR}/generated/files"
        --output "${hg_cartridge}" --manifest "${hg_cartridge_manifest}"
    DEPENDS "${hg_cartridge_script}" "${game_source}/filesystem.mk" ${hg_cartridge_inputs}
    VERBATIM)
add_custom_target(heartgold_cartridge DEPENDS "${hg_cartridge}" "${hg_cartridge_manifest}")
# Resource targets own their producer rules. Keep the file dependencies above
# for invalidation, but do not copy every conversion into the cartridge target.
add_dependencies(heartgold_cartridge ${heartgold_asset_targets})
foreach(name source_cartridge)
    add_test(NAME ${name} COMMAND "${Python3_EXECUTABLE}" -B
        "${PROJECT_SOURCE_DIR}/tests/test_${name}.py")
    set_tests_properties(${name} PROPERTIES ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
endforeach()
add_test(NAME elf_reader COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_elf_reader.py"
    --tool $<TARGET_FILE:hg_o2narc> --work "${PROJECT_BINARY_DIR}")
add_test(NAME asset_indices COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_asset_indices.py"
    --build "${PROJECT_BINARY_DIR}" --tool $<TARGET_FILE:hg_nitroarc>)
set_tests_properties(asset_indices PROPERTIES TIMEOUT 300)
