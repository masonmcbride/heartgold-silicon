# Original HeartGold item-data CSV -> NARC/NAIX pipeline.

file(GLOB hg_csv2bin_sources CONFIGURE_DEPENDS
    "${hg_tools}/csv2bin/*.cpp"
    "${hg_tools}/csv2bin/*.c")

if(NOT hg_csv2bin_sources)
    message(FATAL_ERROR "Original csv2bin sources not found")
endif()

add_executable(hg_csv2bin ${hg_csv2bin_sources})
target_compile_features(hg_csv2bin PRIVATE cxx_std_17)

set(hg_item_source "${game_source}/files/itemtool/itemdata")
set(hg_item_output "${CMAKE_BINARY_DIR}/generated/files/itemtool/itemdata")

set(hg_item_csv "${hg_item_source}/item_data.csv")
set(hg_item_manifest "${hg_item_source}/item_data.txt")
set(hg_item_narc "${hg_item_output}/item_data.narc")
set(hg_item_naix "${hg_item_output}/item_data.naix")

# The original manifest names the constants that csv2bin actually reads.
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${hg_item_manifest}")
file(STRINGS "${hg_item_manifest}" hg_item_columns REGEX "^[^:]+:[^:]+:[^:]+\\.h:")
set(hg_item_constants)
foreach(column IN LISTS hg_item_columns)
    string(REPLACE ":" ";" fields "${column}")
    list(GET fields 2 header)
    list(APPEND hg_item_constants "${game_source}/include/${header}")
endforeach()
list(REMOVE_DUPLICATES hg_item_constants)

add_custom_command(
    OUTPUT "${hg_item_narc}" "${hg_item_naix}"

    COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_item_output}"

    COMMAND $<TARGET_FILE:hg_csv2bin>
        compile
        "${hg_item_csv}"
        "${hg_item_narc}"
        "${hg_item_manifest}"
        -i "${CMAKE_BINARY_DIR}/include"
        -i "${game_source}/include"
        --pad 0xFF
        --naix

    DEPENDS
        hg_csv2bin
        "${hg_item_csv}"
        "${hg_item_manifest}"
        ${hg_item_constants}

    VERBATIM
)

add_custom_target(heartgold_item_data_assets
    DEPENDS "${hg_item_narc}" "${hg_item_naix}")

