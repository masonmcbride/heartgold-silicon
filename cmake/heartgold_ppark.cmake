# Original Pal Park JSON and C records; no runtime header overrides or copies.
set(hg_ppark_source "${game_source}/files/arc")
set(hg_ppark_work "${CMAKE_BINARY_DIR}/generated/ppark")
set(hg_ppark_members "${CMAKE_BINARY_DIR}/generated/files/arc/ppark")
set(hg_ppark_types "${hg_ppark_work}/ppark_data.h")
native_generate(ppark-types "${game_source}/include/catching_show.h" "${hg_ppark_types}")
set(hg_ppark_c "${hg_ppark_work}/ppark.c")
set(hg_ppark_obj "${hg_ppark_work}/ppark.o")
set(hg_ppark_bin "${hg_ppark_members}/000.bin")
set(hg_ppark_dep "${hg_ppark_work}/ppark.d")
add_custom_command(OUTPUT "${hg_ppark_bin}"
    BYPRODUCTS "${hg_ppark_c}" "${hg_ppark_obj}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_ppark_members}"
    COMMAND $<TARGET_FILE:hg_jsonproc>
        "${hg_ppark_source}/ppark.json" "${hg_ppark_source}/ppark.json.txt" "${hg_ppark_c}"
    COMMAND "${CMAKE_C_COMPILER}" --target=armv5te-none-eabi -std=gnu11 -fdata-sections
        -DPOKEHEARTGOLD_GLOBAL_H -DPOKEHEARTGOLD_CATCHING_SHOW_H
        -include "${hg_ppark_types}" -I "${game_source}/include"
        -MMD -MF "${hg_ppark_dep}" -MT "${hg_ppark_bin}" -c "${hg_ppark_c}" -o "${hg_ppark_obj}"
    COMMAND "${HG_ASSET_OBJCOPY}" "--dump-section=.rodata.gData=${hg_ppark_bin}" "${hg_ppark_obj}"
    DEPENDS hg_jsonproc "${hg_ppark_source}/ppark.json" "${hg_ppark_source}/ppark.json.txt" "${hg_ppark_types}"
    DEPFILE "${hg_ppark_dep}"
    VERBATIM)
hg_narc(heartgold_ppark_assets "arc/ppark" "${hg_ppark_members}" "${hg_ppark_bin}")
