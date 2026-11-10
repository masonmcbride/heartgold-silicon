# main.lsf:384 owns wifi_data.o in resident. Only the explicitly verified
# pointer-free records are admitted; this is not a complete-member conversion.
enable_language(ASM)
set(hg_wifi_constants_dir "${PROJECT_BINARY_DIR}/wifi-constants")
set(hg_wifi_constants_script "${CMAKE_CURRENT_LIST_DIR}/native_wifi_constants.py")
set(hg_wifi_constants_source "${hg_wifi_constants_dir}/wifi_constants.S")
add_custom_command(OUTPUT "${hg_wifi_constants_source}" "${hg_wifi_constants_dir}/source.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_wifi_constants_script}"
        --game "${game_source}" --output "${hg_wifi_constants_source}"
        --report "${hg_wifi_constants_dir}/source.json"
    DEPENDS "${game_source}/lib/asm/wifi_data.s" "${hg_wifi_constants_script}"
        "${CMAKE_CURRENT_LIST_DIR}/native_data_ir.py"
        "${CMAKE_CURRENT_LIST_DIR}/native_assembly_data.py"
    VERBATIM)
add_library(heartgold_wifi_constants OBJECT "${hg_wifi_constants_source}")
add_custom_command(OUTPUT "${hg_wifi_constants_dir}/object.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_wifi_constants_script}"
        --game "${game_source}" --validate "$<TARGET_OBJECTS:heartgold_wifi_constants>"
        --report "${hg_wifi_constants_dir}/object.json"
    DEPENDS heartgold_wifi_constants $<TARGET_OBJECTS:heartgold_wifi_constants>
        "${hg_wifi_constants_script}" "${game_source}/lib/asm/wifi_data.s"
        "${CMAKE_CURRENT_LIST_DIR}/native_assembly_data.py"
        "${CMAKE_CURRENT_LIST_DIR}/native_data_ir.py"
    VERBATIM)
add_custom_target(heartgold_wifi_constants_verified DEPENDS "${hg_wifi_constants_dir}/object.json")
# Real original resident archive: ordinary game consumers pull these definitions.
target_sources(heartgold_main PRIVATE $<TARGET_OBJECTS:heartgold_wifi_constants>)
add_dependencies(heartgold_main heartgold_wifi_constants_verified)
