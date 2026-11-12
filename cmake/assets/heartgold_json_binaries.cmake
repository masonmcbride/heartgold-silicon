# Original HeartGold JSON -> ARM assembly -> NitroFS binaries.

find_package(Python3 REQUIRED COMPONENTS Interpreter)

find_program(HG_LLVM_OBJCOPY
    NAMES llvm-objcopy
    HINTS /opt/homebrew/opt/llvm/bin /usr/local/opt/llvm/bin
    REQUIRED)

find_program(HG_LLVM_READELF
    NAMES llvm-readelf
    HINTS /opt/homebrew/opt/llvm/bin /usr/local/opt/llvm/bin
    REQUIRED)

set(hg_json_binary_outputs)

function(hg_add_json_binary relative expected_sha1)
    set(source "${game_source}/${relative}.json")
    set(template "${game_source}/${relative}.json.txt")
    set(output "${PROJECT_BINARY_DIR}/generated/${relative}")

    if(relative MATCHES "pmtel_book$")
        set(output "${output}.dat")
    else()
        set(output "${output}.bin")
    endif()

    get_filename_component(output_dir "${output}" DIRECTORY)

    add_custom_command(
        OUTPUT "${output}"
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/build_heartgold_json_binary.py"
            --jsonproc "$<TARGET_FILE:hg_jsonproc>"
            --clang "${CMAKE_C_COMPILER}"
            --objcopy "${HG_LLVM_OBJCOPY}"
            --readelf "${HG_LLVM_READELF}"
            --source "${source}"
            --template "${template}"
            --output "${output}"
            --work-dir "${PROJECT_BINARY_DIR}/generated/json-binary-work"
            --game "${game_source}"
            --sha1 "${expected_sha1}"
        DEPENDS hg_jsonproc "${source}" "${template}"
            "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/build_heartgold_json_binary.py"
        VERBATIM)

    set(hg_json_binary_outputs
        ${hg_json_binary_outputs} "${output}"
        PARENT_SCOPE)
endfunction()

hg_add_json_binary(
    "files/tel/pmtel_book"
    "d3c4e790e1b02b3a905478a83aa3d2cd5fb13a57")

hg_add_json_binary(
    "files/fielddata/wazaoshie/waza_oshie"
    "2f72b525f5b1cbc7415fc6d055a469bd3a84dbc4")

add_custom_target(heartgold_json_binary_assets
    DEPENDS ${hg_json_binary_outputs})

list(APPEND heartgold_asset_targets heartgold_json_binary_assets)
