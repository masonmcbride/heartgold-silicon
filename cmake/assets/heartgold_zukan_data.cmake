# Original Pokédex assembly data and original O2NARC for normal/Giratina forms.
set(hg_zukan_source "${game_source}/files/application/zukanlist/zkn_data/zukan_data")
set(hg_zukan_output "${PROJECT_BINARY_DIR}/generated/files/application/zukanlist/zkn_data")
set(hg_zukan_work "${PROJECT_BINARY_DIR}/generated/zukan_data")
set(hg_zukan_template "${hg_zukan_work}/zukan_data.json.txt")
native_generate(zukan-template "${hg_zukan_source}.json.txt" "${hg_zukan_template}")
set(hg_zukan_asm "${hg_zukan_work}/zukan_data.s")
add_custom_command(OUTPUT "${hg_zukan_asm}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_zukan_work}" "${hg_zukan_output}"
    COMMAND $<TARGET_FILE:hg_jsonproc> "${hg_zukan_source}.json" "${hg_zukan_template}" "${hg_zukan_asm}"
    DEPENDS hg_jsonproc "${hg_zukan_source}.json" "${hg_zukan_template}"
    VERBATIM)
set(hg_zukan_archives)
foreach(form normal gira)
    set(flags -DPM_ASM)
    set(name zukan_data)
    if(form STREQUAL "gira")
        list(APPEND flags -DGIRA)
        set(name zukan_data_gira)
    endif()
    set(obj "${hg_zukan_work}/${name}.o")
    set(dep "${hg_zukan_work}/${name}.d")
    set(narc "${hg_zukan_output}/${name}.narc")
    set(naix "${hg_zukan_output}/${name}.naix")
    add_custom_command(OUTPUT "${narc}" "${naix}"
        BYPRODUCTS "${obj}"
        COMMAND "${CMAKE_C_COMPILER}" --target=armv5te-none-eabi -x assembler-with-cpp
            ${flags} -I "${game_source}/include" -I "${PROJECT_BINARY_DIR}/include"
            -MMD -MF "${dep}" -MQ "${narc}" -c "${hg_zukan_asm}" -o "${obj}"
        COMMAND $<TARGET_FILE:hg_o2narc> "${obj}" "${narc}" -N -p 0xFF
        DEPENDS "${hg_zukan_asm}" hg_o2narc
        DEPFILE "${dep}"
        VERBATIM)
    list(APPEND hg_zukan_archives "${narc}" "${naix}")
endforeach()
add_custom_target(heartgold_zukan_data_assets DEPENDS ${hg_zukan_archives})

# Original encounter JSON/template and O2NARC, including the original version-
# neutral NAIX spelling rule from zukan_enc.mk (HeartGold is the selected game).
set(hg_enc_source "${game_source}/files/application/zukanlist/zkn_data/zukan_enc")
set(hg_enc_work "${PROJECT_BINARY_DIR}/generated/zukan_enc")
set(hg_enc_template "${hg_enc_work}/zukan_enc.json.txt")
native_generate(zukan-enc-template "${hg_enc_source}.json.txt" "${hg_enc_template}" "${hg_enc_source}.mk")
set(hg_enc_asm "${hg_enc_work}/zukan_enc.s")
set(hg_enc_obj "${hg_enc_work}/zukan_enc_gold.o")
set(hg_enc_narc "${hg_zukan_output}/zukan_enc_gold.narc")
set(hg_enc_index "${hg_zukan_output}/zukan_enc_gold.naix")
set(hg_enc_neutral "${hg_zukan_output}/zukan_enc.naix")
add_custom_command(OUTPUT "${hg_enc_narc}" "${hg_enc_index}" "${hg_enc_neutral}"
    BYPRODUCTS "${hg_enc_asm}" "${hg_enc_obj}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_enc_work}" "${hg_zukan_output}"
    COMMAND $<TARGET_FILE:hg_jsonproc> "${hg_enc_source}.json" "${hg_enc_template}" "${hg_enc_asm}"
    COMMAND "${CMAKE_C_COMPILER}" --target=armv5te-none-eabi -x assembler-with-cpp
        -DPM_ASM -c "${hg_enc_asm}" -o "${hg_enc_obj}"
    COMMAND $<TARGET_FILE:hg_o2narc> "${hg_enc_obj}" "${hg_enc_narc}" -n -p 0x00
    COMMAND "${CMAKE_COMMAND}" -DINPUT=${hg_enc_index} -DOUTPUT=${hg_enc_neutral}
        -P "${CMAKE_CURRENT_LIST_DIR}/neutral_naix.cmake"
    DEPENDS hg_jsonproc hg_o2narc "${hg_enc_source}.json" "${hg_enc_template}"
        "${CMAKE_CURRENT_LIST_DIR}/neutral_naix.cmake" "${hg_enc_source}.mk"
    VERBATIM)
add_custom_target(heartgold_zukan_enc_assets DEPENDS "${hg_enc_narc}" "${hg_enc_index}" "${hg_enc_neutral}")
