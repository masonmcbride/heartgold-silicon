# Adapt the original DWC iterator size assertion for native pointer width.
# Preserve the original Iterator structure and function declarations.

set(hg_dwc_original
    "${game_source}/lib/NitroDWC/src/tree-iterator4.h")
set(hg_dwc_native
    "${CMAKE_BINARY_DIR}/generated/native-headers/tree-iterator4.h")

set_property(DIRECTORY APPEND PROPERTY
    CMAKE_CONFIGURE_DEPENDS "${hg_dwc_original}")

file(READ "${hg_dwc_original}" hg_dwc_text)

set(hg_dwc_original_assert
    "typedef char DwcTreeIteratorSize4[sizeof(Iterator)==4?1:-1];")
set(hg_dwc_native_assert
    "typedef char DwcTreeIteratorSize4[sizeof(Iterator)==sizeof(void*)?1:-1];")

string(FIND "${hg_dwc_text}" "${hg_dwc_original_assert}" hg_dwc_pos)
if(hg_dwc_pos EQUAL -1)
    message(FATAL_ERROR "Original DWC iterator assertion changed")
endif()

string(REPLACE
    "${hg_dwc_original_assert}"
    "${hg_dwc_native_assert}"
    hg_dwc_text "${hg_dwc_text}")

get_filename_component(hg_dwc_dir "${hg_dwc_native}" DIRECTORY)
file(MAKE_DIRECTORY "${hg_dwc_dir}")
file(WRITE "${hg_dwc_native}" "${hg_dwc_text}")

# Preinclude the native header so the original include guard prevents
# the incompatible DS-only assertion from being evaluated.
set_property(
    SOURCE "${game_source}/src/field_transition_tasks.c"
    APPEND PROPERTY COMPILE_OPTIONS
    "-include" "${hg_dwc_native}"
)

# Wi-Fi Plaza also includes the original DWC iterator header.
set_property(
    SOURCE "${game_source}/src/wifi_plaza/wifi_plaza_player_info.c"
    APPEND PROPERTY COMPILE_OPTIONS
    "-include" "${hg_dwc_native}"
)
