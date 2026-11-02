# Build original graphics archives from their original Makefile manifests.
# All conversions and staging happen in build/, never in the source tree.

function(hg_read_make_members result manifest variable)
    # Read the original Makefile manifest without modifying it.
    file(READ "${manifest}" contents)

    # Normalize CRLF and Makefile backslash-newline continuations.
    string(REPLACE "\r\n" "\n" contents "${contents}")
    string(REPLACE "\\\n" " " contents "${contents}")

    # Match one complete assignment, stopping at the next newline.
    string(REGEX MATCH
        "(^|\n)${variable}[ \t]*:=[ \t]*([^\n]*)"
        assignment "${contents}")

    if(NOT assignment)
        message(FATAL_ERROR
            "Missing original manifest variable ${variable}: ${manifest}")
    endif()

    set(values "${CMAKE_MATCH_2}")
    separate_arguments(paths UNIX_COMMAND "${values}")

    if(NOT paths)
        message(FATAL_ERROR
            "Empty original manifest variable ${variable}: ${manifest}")
    endif()

    set(members)
    foreach(member IN LISTS paths)
        get_filename_component(filename "${member}" NAME)
        if(filename STREQUAL "")
            message(FATAL_ERROR
                "Invalid original manifest entry: ${member}")
        endif()
        list(APPEND members "${filename}")
    endforeach()

    set(${result} "${members}" PARENT_SCOPE)
endfunction()

function(hg_manifest_graphics_archive
         target relative manifest member_variable expected_count
         eight_bit_variable four_bit_variable)

    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
        "${manifest}")

    hg_read_make_members(members "${manifest}" "${member_variable}")

    list(LENGTH members count)
    if(NOT count EQUAL expected_count)
        message(FATAL_ERROR
            "${relative}: expected ${expected_count} resources, found ${count}")
    endif()

    set(sorted_members "${members}")
    list(SORT sorted_members)
    if(NOT "${members}" STREQUAL "${sorted_members}")
        message(FATAL_ERROR
            "${relative}: original resource order is not lexical")
    endif()

    set(eight_bit)
    set(four_bit)
    if(NOT "${eight_bit_variable}" STREQUAL "")
        hg_read_make_members(eight_bit "${manifest}" "${eight_bit_variable}")
    endif()
    if(NOT "${four_bit_variable}" STREQUAL "")
        hg_read_make_members(four_bit "${manifest}" "${four_bit_variable}")
    endif()

    set(source "${game_source}/files/${relative}")
    set(stage "${PROJECT_BINARY_DIR}/generated/files/${relative}")
    set(outputs)

    foreach(name IN LISTS members)
        set(input "${source}/${name}")
        set(output "${stage}/${name}")

        if(EXISTS "${input}")
            # Preserve original binary resources without re-encoding.
            add_custom_command(OUTPUT "${output}"
                COMMAND "${CMAKE_COMMAND}" -E make_directory "${stage}"
                COMMAND "${CMAKE_COMMAND}" -E copy_if_different
                    "${input}" "${output}"
                COMMAND "${CMAKE_COMMAND}" -E touch_nocreate "${output}"
                DEPENDS "${input}"
                VERBATIM)

        elseif(name MATCHES "\\.lz$")
            # Original graphics_files_rules.mk: %.lz: %
            string(REGEX REPLACE "\\.lz$" "" raw_name "${name}")
            set(raw "${source}/${raw_name}")
            if(NOT EXISTS "${raw}")
                message(FATAL_ERROR "Missing LZ source: ${raw}")
            endif()

            add_custom_command(OUTPUT "${output}"
                COMMAND "${CMAKE_COMMAND}" -E make_directory "${stage}"
                COMMAND $<TARGET_FILE:hg_nitrogfx> "${raw}" "${output}"
                DEPENDS hg_nitrogfx "${raw}"
                VERBATIM)

        elseif(name MATCHES "\\.NCGR$")
            # PNG -> NCGR flags come from graphics_files_rules.mk,
            # with bit depth selected by the original archive manifest.
            string(REGEX REPLACE "\\.NCGR$" ".png" png_name "${name}")
            set(png "${source}/${png_name}")

            list(FIND eight_bit "${png_name}" index8)
            list(FIND four_bit "${png_name}" index4)

            if(NOT EXISTS "${png}")
                message(FATAL_ERROR "Missing original PNG: ${png}")
            endif()
            if((index8 EQUAL -1 AND index4 EQUAL -1)
               OR (NOT index8 EQUAL -1 AND NOT index4 EQUAL -1))
                message(FATAL_ERROR
                    "${name}: ambiguous original graphics conversion")
            endif()

            set(flags -version101 -sopc)
            if(NOT index8 EQUAL -1)
                list(APPEND flags -bitdepth 8)
            endif()

            add_custom_command(OUTPUT "${output}"
                COMMAND "${CMAKE_COMMAND}" -E make_directory "${stage}"
                COMMAND $<TARGET_FILE:hg_nitrogfx>
                    "${png}" "${output}" ${flags}
                DEPENDS hg_nitrogfx "${png}"
                VERBATIM)

        else()
            message(FATAL_ERROR
                "${relative}: unsupported original member ${name}")
        endif()

        list(APPEND outputs "${output}")
    endforeach()

    # Existing implementation handles original .narcignore/.narcorder
    # metadata and emits both NARC and NAIX.
    hg_narc(${target} "${relative}" "${stage}" ${outputs})
endfunction()

# Original files/demo/opening/gs_opening.mk.
hg_manifest_graphics_archive(
    heartgold_gs_opening_assets
    "demo/opening/gs_opening"
    "${game_source}/files/demo/opening/gs_opening.mk"
    GSOPENING_FILES 106 "" "")

# Original files/demo/title/titledemo.mk.
hg_manifest_graphics_archive(
    heartgold_titledemo_assets
    "demo/title/titledemo"
    "${game_source}/files/demo/title/titledemo.mk"
    TITLEDEMO_DEPS 44
    TITLEDEMO_8BPP_PNGS TITLEDEMO_4BPP_PNGS)

# Extend the same staging/packing pipeline to the remaining overlay manifests.
# Python only reads the inspected Make expressions; original tools emit resources
# and their index headers. There is no independent index-header writer.
set(hg_manifest_reader "${CMAKE_CURRENT_LIST_DIR}/asset_manifest.py")
execute_process(COMMAND "${Python3_EXECUTABLE}" -B "${hg_manifest_reader}"
    --root "${game_source}"
    OUTPUT_VARIABLE hg_manifest_plan COMMAND_ERROR_IS_FATAL ANY)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${hg_manifest_reader}" "${game_source}/graphics_files_rules.mk")
file(CONFIGURE OUTPUT "${PROJECT_BINARY_DIR}/generated/overlay-asset-plan.json"
    CONTENT "${hg_manifest_plan}" @ONLY)
string(JSON hg_archive_count LENGTH "${hg_manifest_plan}")
math(EXPR hg_archive_last "${hg_archive_count} - 1")
set(heartgold_overlay_index_targets)
foreach(a RANGE ${hg_archive_last})
    string(JSON plan GET "${hg_manifest_plan}" ${a})
    string(JSON relative GET "${plan}" relative)
    string(JSON manifest GET "${plan}" manifest)
    set(manifest "${game_source}/${manifest}")
    set(stage "${PROJECT_BINARY_DIR}/generated/files/${relative}")
    set(work "${PROJECT_BINARY_DIR}/generated/asset-work/${relative}")
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${manifest}")
    # Track wildcard inventory changes without running Make or writing upstream.
    file(GLOB original_inventory CONFIGURE_DEPENDS "${game_source}/files/${relative}/*")
    set(recipe_deps "${manifest}" "${game_source}/graphics_files_rules.mk" "${hg_manifest_reader}")
    string(JSON count LENGTH "${plan}" steps)
    math(EXPR last "${count} - 1")
    foreach(i RANGE ${last})
        string(JSON step GET "${plan}" steps ${i})
        string(JSON name GET "${step}" name)
        string(JSON kind GET "${step}" kind)
        string(JSON input GET "${step}" input)
        string(JSON generated ERROR_VARIABLE no_generated GET "${step}" generated)
        if(NOT no_generated)
            set(input "${stage}/${input}")
        endif()
        set(output "${stage}/${name}")
        set(flags)
        string(JSON nflags LENGTH "${step}" flags)
        if(nflags GREATER 0)
            math(EXPR flag_last "${nflags} - 1")
            foreach(f RANGE ${flag_last})
                string(JSON flag GET "${step}" flags ${f})
                list(APPEND flags "${flag}")
            endforeach()
        endif()
        if(kind STREQUAL "copy")
            add_custom_command(OUTPUT "${output}"
                COMMAND "${CMAKE_COMMAND}" -E make_directory "${stage}"
                COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${input}" "${output}"
                COMMAND "${CMAKE_COMMAND}" -E touch_nocreate "${output}"
                DEPENDS "${input}" ${recipe_deps} VERBATIM)
        elseif(kind STREQUAL "gfx")
            set(key)
            if(EXISTS "${input}.key")
                list(APPEND key "${input}.key")
            endif()
            add_custom_command(OUTPUT "${output}"
                COMMAND "${CMAKE_COMMAND}" -E make_directory "${stage}"
                COMMAND $<TARGET_FILE:hg_nitrogfx> "${input}" "${output}" ${flags}
                DEPENDS hg_nitrogfx "${input}" ${key} ${recipe_deps} VERBATIM)
        elseif(kind STREQUAL "json-asm")
            string(JSON template GET "${step}" template)
            set(asm "${work}/${name}.s")
            set(obj "${work}/${name}.o")
            add_custom_command(OUTPUT "${output}"
                BYPRODUCTS "${asm}" "${obj}"
                COMMAND "${CMAKE_COMMAND}" -E make_directory "${stage}" "${work}"
                COMMAND $<TARGET_FILE:hg_jsonproc> "${input}" "${template}" "${asm}"
                COMMAND "${CMAKE_C_COMPILER}" --target=armv5te-none-eabi -x assembler-with-cpp
                    -c "${asm}" -o "${obj}"
                COMMAND "${HG_ASSET_OBJCOPY}" "--dump-section=.rodata=${output}" "${obj}"
                DEPENDS hg_jsonproc "${input}" "${template}" ${recipe_deps} VERBATIM)
        else()
            message(FATAL_ERROR "Unsupported original resource kind: ${kind}")
        endif()
    endforeach()
    set(members)
    string(JSON count LENGTH "${plan}" members)
    math(EXPR last "${count} - 1")
    foreach(i RANGE ${last})
        string(JSON name GET "${plan}" members ${i})
        list(APPEND members "${stage}/${name}")
    endforeach()
    string(MAKE_C_IDENTIFIER "heartgold_${relative}_assets" target)
    string(JSON archive_relative ERROR_VARIABLE unversioned GET "${plan}" archive_relative)
    if(unversioned)
        set(archive_relative "${relative}")
    endif()
    hg_narc(${target} "${archive_relative}" "${stage}" ${members} ${recipe_deps})
    list(APPEND heartgold_overlay_index_targets ${target})
    if(NOT archive_relative STREQUAL relative)
        set(versioned "${PROJECT_BINARY_DIR}/generated/files/${archive_relative}.naix")
        set(neutral "${PROJECT_BINARY_DIR}/generated/files/${relative}.naix")
        add_custom_command(OUTPUT "${neutral}"
            COMMAND "${CMAKE_COMMAND}" -DINPUT=${versioned} -DOUTPUT=${neutral}
                -P "${CMAKE_CURRENT_LIST_DIR}/neutral_naix.cmake"
            DEPENDS "${versioned}" "${CMAKE_CURRENT_LIST_DIR}/neutral_naix.cmake"
            VERBATIM)
        add_custom_target(${target}_neutral DEPENDS "${neutral}")
        # File dependencies alone duplicate producer rules across Make targets.
        add_dependencies(${target}_neutral ${target})
        list(APPEND heartgold_overlay_index_targets ${target}_neutral)
    endif()
endforeach()
