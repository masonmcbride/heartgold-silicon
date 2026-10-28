# Original Pokédex assembly data and original O2NARC for normal/Giratina forms.
set(hg_zukan_source "${game_source}/files/application/zukanlist/zkn_data/zukan_data")
set(hg_zukan_output "${CMAKE_BINARY_DIR}/generated/files/application/zukanlist/zkn_data")
set(hg_zukan_work "${CMAKE_BINARY_DIR}/generated/zukan_data")
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
            ${flags} -I "${game_source}/include" -I "${CMAKE_BINARY_DIR}/include"
            -MMD -MF "${dep}" -MT "${narc}" -c "${hg_zukan_asm}" -o "${obj}"
        COMMAND $<TARGET_FILE:hg_o2narc> "${obj}" "${narc}" -N -p 0xFF
        DEPENDS "${hg_zukan_asm}" hg_o2narc
        DEPFILE "${dep}"
        VERBATIM)
    list(APPEND hg_zukan_archives "${narc}" "${naix}")
endforeach()
add_custom_target(heartgold_zukan_data_assets DEPENDS ${hg_zukan_archives})
