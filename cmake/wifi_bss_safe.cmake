
enable_language(ASM)

set(hg_wifi_bss_dir "${PROJECT_BINARY_DIR}/wifi-bss")
set(hg_wifi_bss_source "${hg_wifi_bss_dir}/safe.S")
set(hg_wifi_bss_driver
    "${CMAKE_CURRENT_LIST_DIR}/native_wifi_bss_safe.py")

add_custom_command(
    OUTPUT "${hg_wifi_bss_source}"
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_wifi_bss_driver}"
        --game "${game_source}"
        --output "${hg_wifi_bss_source}"
        --report "${hg_wifi_bss_dir}/source.json"
    DEPENDS
        "${game_source}/lib/asm/wifi_bss.s"
        "${hg_wifi_bss_driver}"
        "${CMAKE_CURRENT_LIST_DIR}/native_data_ir.py"
    VERBATIM)

add_library(heartgold_wifi_bss_safe OBJECT
    "${hg_wifi_bss_source}")

add_custom_command(
    OUTPUT "${hg_wifi_bss_dir}/object.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${hg_wifi_bss_driver}"
        --game "${game_source}"
        --output "${hg_wifi_bss_source}"
        --report "${hg_wifi_bss_dir}/object.json"
        --validate "$<TARGET_OBJECTS:heartgold_wifi_bss_safe>"
    DEPENDS
        heartgold_wifi_bss_safe
        $<TARGET_OBJECTS:heartgold_wifi_bss_safe>
        "${hg_wifi_bss_driver}"
    VERBATIM)

add_custom_target(heartgold_wifi_bss_safe_verified
    DEPENDS "${hg_wifi_bss_dir}/object.json")

target_sources(heartgold_main PRIVATE
    $<TARGET_OBJECTS:heartgold_wifi_bss_safe>)

add_dependencies(heartgold_main
    heartgold_wifi_bss_safe_verified)
