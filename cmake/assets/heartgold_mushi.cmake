# Original HeartGold Bug-Catching Contest data.
# Source CSV + manifest -> original csv2bin -> NitroFS binary.

set(hg_mushi_outputs)

foreach(stem IN ITEMS mushi_trainer mushi_encount)
    set(source "${game_source}/files/data/mushi/${stem}.csv")
    set(schema "${game_source}/files/data/mushi/${stem}.txt")
    set(output "${PROJECT_BINARY_DIR}/generated/files/data/mushi/${stem}.bin")

    add_custom_command(
        OUTPUT "${output}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory
            "${PROJECT_BINARY_DIR}/generated/files/data/mushi"
        COMMAND $<TARGET_FILE:hg_csv2bin>
            compile "${source}" "${output}" "${schema}"
            -i "${game_source}/include"
        DEPENDS hg_csv2bin "${source}" "${schema}"
        VERBATIM)

    list(APPEND hg_mushi_outputs "${output}")
endforeach()

add_custom_target(heartgold_mushi_assets
    DEPENDS ${hg_mushi_outputs})

list(APPEND heartgold_asset_targets heartgold_mushi_assets)
