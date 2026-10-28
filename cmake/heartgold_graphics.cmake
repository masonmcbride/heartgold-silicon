# Original Nitro graphics conversions. Each specification is input|output|flags.
function(hg_graphics_archive target relative_archive)
    set(source "${game_source}/files/${relative_archive}")
    set(output "${CMAKE_BINARY_DIR}/generated/files/${relative_archive}")
    set(members)
    foreach(spec IN LISTS ARGN)
        string(REPLACE "|" ";" fields "${spec}")
        list(LENGTH fields count)
        if(NOT count EQUAL 3)
            message(FATAL_ERROR "Invalid original graphics conversion: ${spec}")
        endif()
        list(GET fields 0 input_name)
        list(GET fields 1 output_name)
        list(GET fields 2 options)
        separate_arguments(flags UNIX_COMMAND "${options}")
        set(input "${source}/${input_name}")
        if(NOT EXISTS "${input}")
            message(FATAL_ERROR "Missing original graphics source: ${input}")
        endif()
        set(inputs "${input}")
        if(EXISTS "${input}.key")
            list(APPEND inputs "${input}.key")
        endif()
        set(member "${output}/${output_name}")
        add_custom_command(OUTPUT "${member}"
            COMMAND "${CMAKE_COMMAND}" -E make_directory "${output}"
            COMMAND $<TARGET_FILE:hg_nitrogfx> "${input}" "${member}" ${flags}
            DEPENDS hg_nitrogfx ${inputs}
            VERBATIM)
        list(APPEND members "${member}")
    endforeach()
    hg_narc(${target} "${relative_archive}" "${output}" ${members})
endfunction()

# Original files/data/sbox_gra.mk and graphics_files_rules.mk.
hg_graphics_archive(heartgold_sbox_assets "data/sbox_gra"
    "sbox_gra.png|sbox_gra.NCLR|-bitdepth 4 -nopad -pcmp"
    "sbox_gra.png|sbox_gra.NCGR|-version101 -sopc")
hg_graphics_archive(heartgold_camera_assets "graphic/camera_viewfinder"
    "camera_viewfinder.png|camera_viewfinder.NCLR|"
    "camera_viewfinder.png|camera_viewfinder.NCGR.lz|-version101 -sopc"
    "camera_viewfinder.NSCR|camera_viewfinder.NSCR.lz|")

# Original preview_graphic recipes: paired PNG palettes/characters and NSCR data.
set(hg_preview_source "${game_source}/files/fielddata/graphic/preview_graphic/preview_graphic")
foreach(metadata .narcorder .narcignore)
    if(NOT EXISTS "${hg_preview_source}/${metadata}")
        message(FATAL_ERROR "Missing original preview metadata: ${metadata}")
    endif()
endforeach()
file(GLOB hg_preview_pngs CONFIGURE_DEPENDS "${hg_preview_source}/*.png")
file(GLOB hg_preview_screens CONFIGURE_DEPENDS "${hg_preview_source}/*.NSCR")
list(LENGTH hg_preview_pngs hg_preview_png_count)
list(LENGTH hg_preview_screens hg_preview_screen_count)
if(hg_preview_png_count EQUAL 0 OR NOT hg_preview_png_count EQUAL hg_preview_screen_count)
    message(FATAL_ERROR "Unexpected original map preview asset counts")
endif()
set(hg_preview_conversions)
foreach(png IN LISTS hg_preview_pngs)
    get_filename_component(stem "${png}" NAME_WE)
    list(APPEND hg_preview_conversions
        "${stem}.png|${stem}.NCLR|-bitdepth 8 -nopad"
        "${stem}.png|${stem}.NCGR.lz|-bitdepth 8 -version101 -sopc")
endforeach()
foreach(screen IN LISTS hg_preview_screens)
    get_filename_component(name "${screen}" NAME)
    list(APPEND hg_preview_conversions "${name}|${name}.lz|")
endforeach()
hg_graphics_archive(heartgold_preview_assets
    "fielddata/graphic/preview_graphic/preview_graphic" ${hg_preview_conversions})

# These archives already contain original Nintendo binary graphics. Packing their
# read-only directories directly avoids a second copied resource tree.
set(hg_graphics_root "${game_source}/files")
file(GLOB hg_record_members CONFIGURE_DEPENDS
    "${hg_graphics_root}/application/record/record/*.bin"
    "${hg_graphics_root}/application/record/record/*.NCLR")
hg_narc(heartgold_record_assets "application/record/record"
    "${hg_graphics_root}/application/record/record" ${hg_record_members})
file(GLOB hg_plist_members CONFIGURE_DEPENDS
    "${hg_graphics_root}/graphic/plist_gra/*.NANR"
    "${hg_graphics_root}/graphic/plist_gra/*.NCER"
    "${hg_graphics_root}/graphic/plist_gra/*.NCGR"
    "${hg_graphics_root}/graphic/plist_gra/*.NCLR"
    "${hg_graphics_root}/graphic/plist_gra/*.NSCR")
hg_narc(heartgold_plist_assets "graphic/plist_gra"
    "${hg_graphics_root}/graphic/plist_gra" ${hg_plist_members})
file(GLOB hg_item_icon_members CONFIGURE_DEPENDS
    "${hg_graphics_root}/itemtool/itemdata/item_icon/*.NANR"
    "${hg_graphics_root}/itemtool/itemdata/item_icon/*.NCLR"
    "${hg_graphics_root}/itemtool/itemdata/item_icon/*.NCGR"
    "${hg_graphics_root}/itemtool/itemdata/item_icon/*.NCER")
hg_narc(heartgold_item_icon_assets "itemtool/itemdata/item_icon"
    "${hg_graphics_root}/itemtool/itemdata/item_icon" ${hg_item_icon_members})

# Original Name Entry assets: palettes are copied, other binary graphics compressed.
set(hg_namein_source "${hg_graphics_root}/data/namein")
set(hg_namein_output "${CMAKE_BINARY_DIR}/generated/files/data/namein")
file(GLOB hg_namein_sources CONFIGURE_DEPENDS "${hg_namein_source}/namein_*")
list(LENGTH hg_namein_sources hg_namein_count)
if(NOT hg_namein_count EQUAL 19)
    message(FATAL_ERROR "Expected 19 original namein assets, found ${hg_namein_count}")
endif()
set(hg_namein_members)
foreach(input IN LISTS hg_namein_sources)
    get_filename_component(name "${input}" NAME)
    if(name MATCHES "\\.NCLR$")
        set(output "${hg_namein_output}/${name}")
        add_custom_command(OUTPUT "${output}"
            COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_namein_output}"
            COMMAND "${CMAKE_COMMAND}" -E copy "${input}" "${output}"
            DEPENDS "${input}" VERBATIM)
    else()
        set(output "${hg_namein_output}/${name}.lz")
        add_custom_command(OUTPUT "${output}"
            COMMAND "${CMAKE_COMMAND}" -E make_directory "${hg_namein_output}"
            COMMAND $<TARGET_FILE:hg_nitrogfx> "${input}" "${output}"
            DEPENDS hg_nitrogfx "${input}" VERBATIM)
    endif()
    list(APPEND hg_namein_members "${output}")
endforeach()
hg_narc(heartgold_namein_assets "data/namein" "${hg_namein_output}" ${hg_namein_members})
