# ARM64 party-menu callback adaptation. Original sources remain unchanged.

set(hg_party_list_src "${game_source}/src/party_menu_list_items.c")
set(hg_party_menu_src "${game_source}/src/party_menu.c")
set(hg_party_out "${CMAKE_BINARY_DIR}/native-src")

set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${hg_party_list_src}" "${hg_party_menu_src}")

file(READ "${hg_party_list_src}" hg_party_list)
file(READ "${hg_party_menu_src}" hg_party_menu)

# Derive native function-pointer dispatch from the original action table.
string(REGEX MATCHALL
    "\\[PARTY_MON_CONTEXT_MENU_[A-Z0-9_]+\\][ \t]*=[ \t]*\\(u32\\)PartyMonContextMenuAction_[A-Za-z0-9_]+"
    hg_party_entries "${hg_party_list}")

list(LENGTH hg_party_entries hg_party_count)
if(hg_party_count LESS 25)
    message(FATAL_ERROR "Original party-menu action table changed")
endif()

set(hg_party_dispatch "")
foreach(entry IN LISTS hg_party_entries)
    string(REGEX REPLACE "^\\[([^]]+)\\].*$" "\\1" id "${entry}")
    string(REGEX REPLACE "^.*\\(u32\\)" "" callback "${entry}")

    string(REPLACE "(u32)${callback}" "${id}"
        hg_party_list "${hg_party_list}")

    string(APPEND hg_party_dispatch
        "    [${id}] = ${callback},\n")
endforeach()

string(APPEND hg_party_list
    "\nvoid HG_PartyMenu_InvokeAction(u32 action, PartyMenu *menu, int *state) {\n"
    "    static const PartyMonContextMenuActionFunc actions[PARTY_MON_CONTEXT_MENU_MAX] = {\n"
    "${hg_party_dispatch}"
    "    };\n"
    "    if (action >= PARTY_MON_CONTEXT_MENU_MAX || !actions[action])\n"
    "        __builtin_trap();\n"
    "    actions[action](menu, state);\n"
    "}\n")

set(hg_party_prototype
    "struct PartyMenu;\n"
    "extern void HG_PartyMenu_InvokeAction(unsigned int, struct PartyMenu *, int *);\n")

foreach(argument "&result" "(int *)pState")
    set(old "((PartyMonContextMenuActionFunc)func)(partyMenu, ${argument});")
    set(new "HG_PartyMenu_InvokeAction(func, partyMenu, ${argument});")
    string(FIND "${hg_party_menu}" "${old}" pos)
    if(pos EQUAL -1)
        message(FATAL_ERROR "Original party-menu dispatch changed: ${old}")
    endif()
    string(REPLACE "${old}" "${new}" hg_party_menu "${hg_party_menu}")
endforeach()

file(MAKE_DIRECTORY "${hg_party_out}")
file(WRITE "${hg_party_out}/party_menu_list_items.c" "${hg_party_list}")
file(WRITE "${hg_party_out}/party_menu.c"
    "${hg_party_prototype}${hg_party_menu}")

foreach(name party_menu_list_items party_menu)
    list(FIND game_sources "${game_source}/src/${name}.c" pos)
    if(pos EQUAL -1)
        message(FATAL_ERROR "Original ${name}.c missing from game_sources")
    endif()
    list(REMOVE_ITEM game_sources "${game_source}/src/${name}.c")
    list(APPEND game_sources "${hg_party_out}/${name}.c")
endforeach()
