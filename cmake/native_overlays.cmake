# Explicitly selected local-fork integration; preserve original image membership.
enable_language(ASM)
# The same declared-output generator handles static and overlay data members.
include("${PROJECT_BINARY_DIR}/native-graph/main-data.cmake")
target_sources(heartgold_main PRIVATE ${hg_main_data_sources})
find_program(HG_NATIVE_OTOOL NAMES otool REQUIRED)
set(HEARTGOLD_NATIVE_EXTRA_OVERLAYS "" CACHE STRING "Explicit additional original overlay names")
set(hg_overlay_manifest "${CMAKE_CURRENT_LIST_DIR}/native_overlay_manifest.py")
set(overlay_link_dir "${PROJECT_BINARY_DIR}/native-overlays")
set(hg_overlay_select --supported --select OVY_36 --select intro_title --select OVY_62 --select ds_protect --select OVY_39 --select OVY_40 --select OVY_41)
target_sources(heartgold_main PRIVATE "${PROJECT_SOURCE_DIR}/hardware_drivers/graphics/nsbta_callback.c")
foreach(name IN LISTS HEARTGOLD_NATIVE_EXTRA_OVERLAYS)
    list(APPEND hg_overlay_select --select "${name}")
endforeach()
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${hg_overlay_manifest}" "${CMAKE_CURRENT_LIST_DIR}/native_assembly_data.py"
    "${CMAKE_CURRENT_LIST_DIR}/native_image_graph.py" "${CMAKE_CURRENT_LIST_DIR}/native_data_ir.py"
    "${CMAKE_CURRENT_LIST_DIR}/native_abi.py"
    "${CMAKE_CURRENT_LIST_DIR}/native_data_layouts.py" "${CMAKE_CURRENT_LIST_DIR}/native_data_layouts.json"
    "${CMAKE_CURRENT_LIST_DIR}/native_image_policy.json")
# Original provider closure: GTS (OVY_70) and Nintendo WFC (OVY_72).
# Verified original WFC data conversion and provider closure.
list(APPEND hg_overlay_select --select OVY_72)
# Original GameStats HTTP provider; both assembly members validated.
list(APPEND hg_overlay_select --select OVY_38)
# Original GTS provider; gts_data.o validated with 119 relocations.
list(APPEND hg_overlay_select --select OVY_70)
execute_process(COMMAND "${Python3_EXECUTABLE}" -B "${hg_overlay_manifest}"
    --game "${game_source}" --adapted-dir "${native_root}" --out "${overlay_link_dir}" ${hg_overlay_select}
    COMMAND_ERROR_IS_FATAL ANY)
include("${overlay_link_dir}/selection.cmake")
if("45" IN_LIST hg_selected_overlay_ids)

# HEARTGOLD_OVY45_NATIVE_SOURCE_OVERRIDE
# Retain pristine pinned source; compile this explicitly reviewed
# native ABI adaptation for OVY_45 only.
set(_hg_ovy45_adaptation
    "${CMAKE_SOURCE_DIR}/native-adaptations/OVY_45/lobby_chat_remove_channel.cpp"
)
if(NOT EXISTS "${_hg_ovy45_adaptation}")
    message(FATAL_ERROR "OVY_45 native C++ adaptation is missing")
endif()
set(_hg_ovy45_original_found FALSE)
foreach(_hg_ovy45_source IN LISTS hg_overlay_45_sources)
    if("${_hg_ovy45_source}" MATCHES
       "(^|/)src/lobby/lobby_chat_remove_channel[.]cpp$")
        list(REMOVE_ITEM hg_overlay_45_sources "${_hg_ovy45_source}")
        list(APPEND hg_overlay_45_sources "${_hg_ovy45_adaptation}")
        set(_hg_ovy45_original_found TRUE)
    endif()
endforeach()
if(NOT _hg_ovy45_original_found)
    message(FATAL_ERROR
        "OVY_45 source override failed: original member not located"
    )
endif()
endif()

set(overlay_archives)

# HEARTGOLD_OVY45_NATIVE_GET_WORK_WRAPPER
# Select the original C implementation through a native-only
# translation-unit wrapper; leave the pinned checkout untouched.
if("45" IN_LIST hg_selected_overlay_ids)
    set(_hg_ovy45_get_work_original_found FALSE)
    foreach(_hg_ovy45_source IN LISTS hg_overlay_45_sources)
        if("${_hg_ovy45_source}" MATCHES
           "(^|/)src/lobby/ppw_lobby_get_work[.]c$")
            list(REMOVE_ITEM hg_overlay_45_sources "${_hg_ovy45_source}")
            list(APPEND hg_overlay_45_sources
                "${CMAKE_SOURCE_DIR}/native-adaptations/OVY_45/ppw_lobby_get_work_native.c")
            set(_hg_ovy45_get_work_original_found TRUE)
        endif()
    endforeach()
    if(NOT _hg_ovy45_get_work_original_found)
        message(FATAL_ERROR
            "OVY_45 native get-work wrapper: original member not found")
    endif()
endif()

foreach(id IN LISTS hg_selected_overlay_ids)
    set(target ${hg_overlay_${id}_target})
    if(TARGET ${target})
        set_property(TARGET ${target} PROPERTY SOURCES "${hg_overlay_${id}_sources}")
    else()
        add_library(${target} STATIC ${hg_overlay_${id}_sources})
        target_compile_definitions(${target} PRIVATE "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
        target_include_directories(${target} PRIVATE "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
        target_compile_options(${target} PRIVATE "$<$<COMPILE_LANGUAGE:C,CXX>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>")
        target_link_libraries(${target} PRIVATE nitro_config)
        add_dependencies(${target} heartgold_overlay_native_sources heartgold_native_headers fx_constants ${heartgold_asset_targets})
    endif()
    list(APPEND overlay_archives ${target})
    set(hg_overlay_${id}_archive ${target})
endforeach()

# Original dwc_main.c; native-only storage for its control pointer.
# The complete dwc_lib_bss.o remains blocked by independent ABI contracts.
set(hg_dwc_control_storage
    "${PROJECT_BINARY_DIR}/native-overlays/dwc_control_state.c")
file(WRITE "${hg_dwc_control_storage}" [=[
#include <stddef.h>
#include <dwc/dwc_main_internal.h>

/* Original guest: pointer word at +0, socket error word at +4.
 * Native: full-width pointer and separate error storage.
 */
DwcControl *gDwcControl = NULL;
int gDwcGt2SocketError = 0;
_Static_assert(sizeof(gDwcControl) == sizeof(void *),
               "native DWC pointer width");
_Static_assert(sizeof(gDwcGt2SocketError) == 4,
               "original socket-error word width");
]=])
add_library(hg_dwc_main STATIC
    "${native_root}/lib/NitroDWC/src/dwc_main.c"
    "${native_root}/lib/NitroDWC/src/ap_connect_control.c"
    "${native_root}/lib/NitroDWC/src/ap_connect.c"
    "${native_root}/lib/NitroDWC/src/auth_client.c"
    "${native_root}/lib/NitroDWC/src/auth_netcheck.c"
    "${native_root}/lib/NitroDWC/src/auth_http.c"
    "${native_root}/lib/NitroDWC/src/auth_request.c"
    "${native_root}/lib/NitroDWC/src/friend_manager.c"
    "${native_root}/lib/NitroDWC/src/match_setup.c"
    "${native_root}/lib/NitroDWC/src/transport.c"
    "${native_root}/lib/NitroDWC/src/gs_platform.c"
    "${native_root}/lib/NitroDWC/src/gp_api.c"
    "${hg_dwc_control_storage}")
# Preserve the original writable section and bytes of the five common strings.
# This partial range does not claim admission of the complete mixed data member.
set(hg_dwc_status_strings "${PROJECT_BINARY_DIR}/native-overlays/dwc_status_strings.S")
native_generate(native "${game_source}/lib/NitroDWC/asm/dwc_lib_data.s"
    "${hg_dwc_status_strings}"
    "${CMAKE_CURRENT_LIST_DIR}/native_data_ir.py"
    "${CMAKE_CURRENT_LIST_DIR}/native_assembly_data.py")
target_sources(hg_dwc_main PRIVATE "${hg_dwc_status_strings}")
# Original OVY_0 server-time storage: 4 + 8 + 8 bytes.
# One contiguous record; the labels are aliases into that record.
set(hg_dwc_server_time_storage
    "${PROJECT_BINARY_DIR}/native-overlays/dwc_server_time_state.S")
file(WRITE "${hg_dwc_server_time_storage}" [=[
.section __DATA,__data
.p2align 2
.globl _gDwcServerTime
.globl _ov00_0221A738
.globl _ov00_0221A740
_gDwcServerTime:
    .space 4
_ov00_0221A738:
    .space 8
_ov00_0221A740:
    .space 8
]=])
target_sources(hg_dwc_main PRIVATE "${hg_dwc_server_time_storage}")


# BEGIN REVIEWED OVY_0 COMMUNICATIONS PROVIDERS
# Original OVY_0 providers, verified against main.lsf.
# Existing status/Wi-Fi providers remain separately owned.
target_sources(hg_dwc_main PRIVATE
    "${native_root}/lib/NitroDWC/src/available_check_poll.c"
    "${native_root}/lib/NitroDWC/src/dwc_login.c"
    "${native_root}/lib/NitroDWC/src/friend_callback.c"
    "${native_root}/lib/NitroDWC/src/friend_list.c"
    "${native_root}/lib/NitroDWC/src/gp_buffer.c"
    "${native_root}/lib/NitroDWC/src/gp_connect.c"
    "${native_root}/lib/NitroDWC/src/gp_main.c"
    "${native_root}/lib/NitroDWC/src/gp_operation.c"
    "${native_root}/lib/NitroDWC/src/gp_peer.c"
    "${native_root}/lib/NitroDWC/src/gp_search.c"
    "${native_root}/lib/NitroDWC/src/gp_utility.c"
    "${native_root}/lib/NitroDWC/src/gt_buffer.c"
    "${native_root}/lib/NitroDWC/src/gt_connection.c"
    "${native_root}/lib/NitroDWC/src/gt_socket.c"
    "${native_root}/lib/NitroDWC/src/match_browse.c"
    "${native_root}/lib/NitroDWC/src/match_command.c"
    "${native_root}/lib/NitroDWC/src/match_connect.c"
    "${native_root}/lib/NitroDWC/src/match_join.c"
    "${native_root}/lib/NitroDWC/src/match_sync.c"
    "${native_root}/lib/NitroDWC/src/nat_negotiate.c"
    "${native_root}/lib/NitroDWC/src/query_report_init.c"
    "${native_root}/lib/NitroDWC/src/sb_query_engine.c"
    "${native_root}/lib/NitroDWC/src/sb_server.c"
    "${native_root}/lib/NitroDWC/src/sb_serverlist.c"
    "${native_root}/lib/NitroDWC/src/server_report.c"
    "${native_root}/src/voice_chat_conference.c"
)
# END REVIEWED OVY_0 COMMUNICATIONS PROVIDERS

# BEGIN ORIGINAL THREE-C PROVIDER BATCH
target_sources(hg_dwc_main PRIVATE
    "${native_root}/lib/NitroDWC/src/persist_data.c")

target_sources(heartgold_main PRIVATE
    "${game_source}/lib/NitroDWC/src/dwc_auth_wifi_id.c"
    "${game_source}/lib/NitroDWC/src/dwc_nvram.c")
# END ORIGINAL THREE-C PROVIDER BATCH

target_compile_definitions(hg_dwc_main PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
target_include_directories(hg_dwc_main PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_options(hg_dwc_main PRIVATE
    "$<$<COMPILE_LANGUAGE:C,CXX>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>")
target_link_libraries(hg_dwc_main PRIVATE nitro_config)
add_dependencies(hg_dwc_main heartgold_overlay_native_sources heartgold_native_headers fx_constants)
# Resident machine code retains its original OVY_0 provider identity. This
# archive has the native ABI already used by the existing Wi-Fi consumer;
# guest32-account/provider.a remains a separate representation.
target_link_libraries(heartgold PRIVATE hg_dwc_main)

set(hg_ovy0_wifi_source "${native_root}/src/wifi_connection.c")
add_library(hg_ovy0_wifi_code OBJECT
    "${hg_ovy0_wifi_source}"
    "${native_root}/src/voice_chat.c")
target_compile_definitions(hg_ovy0_wifi_code PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
target_include_directories(hg_ovy0_wifi_code PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_options(hg_ovy0_wifi_code PRIVATE
    "$<$<COMPILE_LANGUAGE:C,CXX>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>")
target_link_libraries(hg_ovy0_wifi_code PRIVATE nitro_config)
set_target_properties(hg_ovy0_wifi_code PROPERTIES POSITION_INDEPENDENT_CODE ON)
add_dependencies(hg_ovy0_wifi_code heartgold_overlay_native_sources heartgold_native_headers fx_constants)

get_target_property(overlay_sdk_targets nitro_sdk INTERFACE_LINK_LIBRARIES)
set(overlay_main_targets heartgold_main heartgold_runtime heartgold_sound_storage native_host hg_dwc_main ${overlay_sdk_targets})
if(TARGET heartgold_guest32_account)
    list(APPEND overlay_main_targets heartgold_guest32_account heartgold_guest32_crc heartgold_guest32_std heartgold_guest32_runtime heartgold_guest32_mi)
endif()
set(overlay_link_args)
set(overlay_link_dependencies)
foreach(target IN LISTS overlay_main_targets)
    list(APPEND overlay_link_args --main "$<TARGET_FILE:${target}>")
    list(APPEND overlay_link_dependencies ${target} "$<TARGET_FILE:${target}>")
endforeach()
if(TARGET heartgold_guest32_account)
    foreach(name account crc std)
        set(manifest "${PROJECT_BINARY_DIR}/guest32-${name}/providers.json")
        list(APPEND overlay_link_args --provider-manifest "${manifest}")
        list(APPEND overlay_link_dependencies "${manifest}")
    endforeach()
    list(APPEND overlay_link_args --provider-manifest "${guest_mi_manifest}")
    list(APPEND overlay_link_dependencies "${guest_mi_manifest}" heartgold_guest32_mi_manifest)
endif()
foreach(id IN LISTS hg_selected_overlay_ids)
    set(target ${hg_overlay_${id}_archive})
    list(APPEND overlay_link_args --overlay "${id}=$<TARGET_FILE:${target}>")
    list(APPEND overlay_link_dependencies ${target} "$<TARGET_FILE:${target}>")
endforeach()
set(overlay_link_dir "${PROJECT_BINARY_DIR}/native-overlays")
set(overlay_imports "${overlay_link_dir}/imports.rsp")
set(overlay_exports "${overlay_link_dir}/main-exports.txt")
set(overlay_contracts "${overlay_link_dir}/providers.json")
set(overlay_registry "${overlay_link_dir}/provider-registry.json")
set(hg_interface_outputs "${overlay_link_dir}/interfaces/main.tbd")
# Compile the common consumer independently so the existing resident-provider
# graph can derive its actual imports without a shared-library dependency cycle.
add_library(hg_dwc_status_code OBJECT
    "${native_root}/lib/NitroDWC/src/net_common.c"
    "${PROJECT_SOURCE_DIR}/hardware_drivers/wireless/dwc_common_state.c")
target_compile_definitions(hg_dwc_status_code PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
target_include_directories(hg_dwc_status_code PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_options(hg_dwc_status_code PRIVATE
    "$<$<COMPILE_LANGUAGE:C,CXX>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>")
target_link_libraries(hg_dwc_status_code PRIVATE nitro_config)
add_dependencies(hg_dwc_status_code heartgold_overlay_native_sources heartgold_native_headers fx_constants)
foreach(id IN LISTS hg_selected_overlay_ids)
    list(APPEND hg_interface_outputs "${overlay_link_dir}/interfaces/image_${id}.tbd"
        "${overlay_link_dir}/image_${id}.rsp")
endforeach()
add_custom_command(OUTPUT ${hg_interface_outputs} "${overlay_imports}" "${overlay_exports}" "${overlay_contracts}" "${overlay_registry}"
    COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_LIST_DIR}/native_overlay_link.py"
        --nm "${CMAKE_NM}" --image-graph "${PROJECT_BINARY_DIR}/native-graph/images.json" ${overlay_link_args}
        --resident-owner "$<TARGET_FILE:hg_dwc_main>=OVY_0"
        --resident-root _DWC_GetMyAID --resident-root _DWC_ProcessFriendsMatch
        "$<$<BOOL:$<TARGET_OBJECTS:hg_ovy0_wifi_code>>:--resident-consumer;$<JOIN:$<TARGET_OBJECTS:hg_ovy0_wifi_code>,;--resident-consumer;>>"
        "--resident-consumer;$<JOIN:$<TARGET_OBJECTS:hg_dwc_status_code>,;--resident-consumer;>"
        --imports "${overlay_imports}" --exports "${overlay_exports}" --contracts "${overlay_contracts}"
    COMMAND "${CMAKE_COMMAND}" -E touch ${hg_interface_outputs}
        "${overlay_imports}" "${overlay_exports}" "${overlay_contracts}"
    DEPENDS ${overlay_link_dependencies} hg_ovy0_wifi_code $<TARGET_OBJECTS:hg_ovy0_wifi_code>
        hg_dwc_status_code $<TARGET_OBJECTS:hg_dwc_status_code>
        "${CMAKE_CURRENT_LIST_DIR}/native_overlay_link.py"
        "${CMAKE_CURRENT_LIST_DIR}/native_provider_registry.py" "${PROJECT_BINARY_DIR}/native-graph/images.json"
    COMMAND_EXPAND_LISTS VERBATIM)
add_custom_target(heartgold_overlay_link_contract DEPENDS ${hg_interface_outputs} "${overlay_imports}" "${overlay_exports}" "${overlay_contracts}" "${overlay_registry}")

# OVY_0 original-code partial provider: independently closed Wi-Fi exports.
# Do not duplicate these identities if full OVY_0 is selected.
if("0" IN_LIST hg_selected_overlay_ids)
    message(FATAL_ERROR
        "OVY_0 Wi-Fi subset conflicts with complete OVY_0 ownership")
endif()

add_library(hg_ovy0_wifi_subset SHARED $<TARGET_OBJECTS:hg_ovy0_wifi_code>)
target_compile_definitions(hg_ovy0_wifi_subset PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
target_include_directories(hg_ovy0_wifi_subset PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_options(hg_ovy0_wifi_subset PRIVATE
    "$<$<COMPILE_LANGUAGE:C,CXX>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>")
target_link_libraries(hg_ovy0_wifi_subset PRIVATE
    nitro_config "${overlay_link_dir}/interfaces/main.tbd")
target_link_options(hg_ovy0_wifi_subset PRIVATE
    "LINKER:-dead_strip"
    "LINKER:-exported_symbol,_WifiConnection_GetTargetFriendIndex"
    "LINKER:-exported_symbol,_WifiConnection_ClassifyErrorCode"
    "LINKER:-exported_symbol,_WifiConnection_GetNumConnectionHost"
    "LINKER:-exported_symbol,_WifiConnection_SetClientCallback"
    "LINKER:-exported_symbol,_WifiConnection_StartAnybodyMatchmaking"
    "LINKER:-exported_symbol,_WifiConnection_StartVoiceChat"
    "LINKER:-exported_symbol,_WifiConnection_StopVoiceChat"
    "LINKER:-exported_symbol,_WifiConnection_SetDisconnectCallback"
    "LINKER:-exported_symbol,_VoiceChat_Init"
    "LINKER:-exported_symbol,_VoiceChat_SetEndCallback"
    "LINKER:-exported_symbol,_VoiceChat_Shutdown"
    "LINKER:-exported_symbol,_WifiConnection_ClearFriendDataChanged"
    "LINKER:-exported_symbol,_WifiConnection_GetFriendStatus"
    "LINKER:-exported_symbol,_WifiConnection_GetNewClientIndex"
    "LINKER:-exported_symbol,_WifiConnection_GetVoiceActivity"
    "LINKER:-exported_symbol,_WifiConnection_IsFriendDataChanged"
    "LINKER:-exported_symbol,_WifiConnection_IsVoiceChatEnabled"
    "LINKER:-exported_symbol,_WifiConnection_ResetStopServerMatching"
    "LINKER:-exported_symbol,_WifiConnection_SetConnectFilterCallback"
    "LINKER:-exported_symbol,_WifiConnection_SetDisconnectWhenAlone"
    "LINKER:-exported_symbol,_WifiConnection_SetExtraHeapEnabled"
    "LINKER:-exported_symbol,_WifiConnection_SetFriendStatusBuffer"
    "LINKER:-exported_symbol,_WifiConnection_SetOwnStatusData"
    "LINKER:-exported_symbol,_WifiConnection_SetVoiceChatEnabled"
    "LINKER:-exported_symbol,_WifiConnection_StopServerMatching")
# BEGIN PERMANENT hg_ovy0_wifi_subset COMMUNICATIONS EXPORTS
# Original compiled providers; preserve existing state ownership.
target_link_options(hg_ovy0_wifi_subset PRIVATE
    "LINKER:-exported_symbol,_WifiConnection_CheckError"
    "LINKER:-exported_symbol,_WifiConnection_Disconnect"
    "LINKER:-exported_symbol,_WifiConnection_FinishDisconnect"
    "LINKER:-exported_symbol,_WifiConnection_GetAid"
    "LINKER:-exported_symbol,_WifiConnection_Init"
    "LINKER:-exported_symbol,_WifiConnection_SendFromHost"
    "LINKER:-exported_symbol,_WifiConnection_SendToAll"
    "LINKER:-exported_symbol,_WifiConnection_SendToHost"
    "LINKER:-exported_symbol,_WifiConnection_SetErrorCallback"
    "LINKER:-exported_symbol,_WifiConnection_SetReceiveCallbacks"
    "LINKER:-exported_symbol,_WifiConnection_SetVoiceUnmuted"
    "LINKER:-exported_symbol,_WifiConnection_Shutdown"
    "LINKER:-exported_symbol,_WifiConnection_StartMatchmaking"
    "LINKER:-exported_symbol,_WifiConnection_Update"
    "LINKER:-exported_symbol,_WifiConnection_UpdateLogin"
    "LINKER:-exported_symbol,_gVoiceChat"
)
# END PERMANENT hg_ovy0_wifi_subset COMMUNICATIONS EXPORTS
set_target_properties(hg_ovy0_wifi_subset PROPERTIES
    OUTPUT_NAME "heartgold_ovy0_wifi_subset"
    LIBRARY_OUTPUT_DIRECTORY "${overlay_link_dir}"
    INSTALL_NAME_DIR "@rpath"
    BUILD_WITH_INSTALL_NAME_DIR TRUE)
add_dependencies(hg_ovy0_wifi_subset
    heartgold_overlay_native_sources
    heartgold_native_headers
    fx_constants
    heartgold_overlay_link_contract)


# Original NitroDWC OVY_0 state and two independently closed exports.
# Preserve a single runtime instance of gDwcNetError across consumers.
if("0" IN_LIST hg_selected_overlay_ids)
    message(FATAL_ERROR
        "NitroDWC status provider conflicts with complete OVY_0 ownership")
endif()

add_library(hg_dwc_status SHARED $<TARGET_OBJECTS:hg_dwc_status_code>)
target_compile_definitions(hg_dwc_status PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
target_include_directories(hg_dwc_status PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_options(hg_dwc_status PRIVATE
    "$<$<COMPILE_LANGUAGE:C,CXX>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>")
target_link_libraries(hg_dwc_status PRIVATE
    nitro_config "${overlay_link_dir}/interfaces/main.tbd")
target_link_options(hg_dwc_status PRIVATE
    "LINKER:-dead_strip"
    "LINKER:-exported_symbol,_gDwcNetError"
    "LINKER:-exported_symbol,_gDwcNetAllocator"
    "LINKER:-exported_symbol,_gDwcNetConnection"
    "LINKER:-exported_symbol,_DWC_UpdateConnection"
    "LINKER:-exported_symbol,_DWC_ClearError"
    "LINKER:-exported_symbol,_DWC_GetLinkLevel"
    "LINKER:-exported_symbol,_DWCi_SetError"
    "LINKER:-exported_symbol,_DWCi_IsError"
    "LINKER:-exported_symbol,_DWC_GetLastErrorEx"
    "LINKER:-exported_symbol,_DWC_GetLastError"
    "LINKER:-exported_symbol,_DWC_SetMemFunc"
    "LINKER:-exported_symbol,_DWC_AllocEx"
    "LINKER:-exported_symbol,_DWC_Realloc"
    "LINKER:-exported_symbol,_DWC_ReallocEx"
    "LINKER:-exported_symbol,_DWCi_GetAllocHeader"
    "LINKER:-exported_symbol,_DWCi_InitAllocHeader"
    "LINKER:-exported_symbol,_DWCi_GetAllocSize"
    "LINKER:-exported_symbol,_DWCi_GsMalloc"
    "LINKER:-exported_symbol,_DWCi_GsRealloc"
    "LINKER:-exported_symbol,_DWCi_GsFree"
    "LINKER:-exported_symbol,_DWC_Alloc"
    "LINKER:-exported_symbol,_DWC_CheckInet"
    "LINKER:-exported_symbol,_DWC_CleanupInet"
    "LINKER:-exported_symbol,_DWC_ConnectInetAsync"
    "LINKER:-exported_symbol,_DWC_Free"
    "LINKER:-exported_symbol,_DWC_GetApInfo"
    "LINKER:-exported_symbol,_DWC_GetDateTime"
    "LINKER:-exported_symbol,_DWC_GetInetStatus"
    "LINKER:-exported_symbol,_DWC_InitInetEx"
    "LINKER:-exported_symbol,_DWC_NASLoginAsync"
    "LINKER:-exported_symbol,_DWC_NASLoginProcess"
    "LINKER:-exported_symbol,_DWC_ProcessInet"
    "LINKER:-exported_symbol,_DWC_SVLGetTokenAsync"
    "LINKER:-exported_symbol,_DWC_SVLProcess"
    "LINKER:-exported_symbol,_DWC_SetAuthServer")
# BEGIN PERMANENT hg_dwc_status COMMUNICATIONS EXPORTS
# Original compiled providers; preserve existing state ownership.
target_link_options(hg_dwc_status PRIVATE
    "LINKER:-exported_symbol,_DWC_AddCommonKeyValueString"
    "LINKER:-exported_symbol,_DWC_GetCommonValueString"
    "LINKER:-exported_symbol,_DWC_SetCommonKeyValueString"
    "LINKER:-exported_symbol,_DWCi_Base64Decode"
    "LINKER:-exported_symbol,_DWCi_Base64Encode"
    "LINKER:-exported_symbol,_DWCi_GetRandom"
)
# END PERMANENT hg_dwc_status COMMUNICATIONS EXPORTS
set_target_properties(hg_dwc_status PROPERTIES
    OUTPUT_NAME "heartgold_dwc_status"
    LIBRARY_OUTPUT_DIRECTORY "${overlay_link_dir}"
    INSTALL_NAME_DIR "@rpath"
    BUILD_WITH_INSTALL_NAME_DIR TRUE)
# BEGIN PERMANENT WIFI TO DWC DEPENDENCY
# Original Wi-Fi code calls the resident DWC internet/error services.
# Bind through the existing dylib, preserving single-instance DWC state.
target_link_libraries(hg_ovy0_wifi_subset PRIVATE hg_dwc_status)
# END PERMANENT WIFI TO DWC DEPENDENCY
add_dependencies(hg_dwc_status
    heartgold_overlay_native_sources
    heartgold_native_headers
    fx_constants
    heartgold_overlay_link_contract)

set(hg_dwc_status_consumer_ids 12 39 45 73 75)

# Consolidated original-provider admission attempt. Its outputs remain staged
# until caller ABI, storage and lifecycle obligations are all established.
# Never link these guest entries under the native partial-provider identities.
if(TARGET heartgold_guest32_provider_closure)
    add_custom_target(heartgold_guest32_network_admission
        COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_LIST_DIR}/guest32_admission.py"
            --build "${PROJECT_BINARY_DIR}" --closure "${guest32_provider_dir}"
            --out "${overlay_link_dir}/guest32-admission"
            --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>
        BYPRODUCTS "${overlay_link_dir}/guest32-admission/admission.json"
            "${overlay_link_dir}/guest32-admission/libheartgold_image_0.dylib"
            "${overlay_link_dir}/guest32-admission/libheartgold_image_38.dylib"
        DEPENDS heartgold_guest32_provider_closure heartgold_overlay_link_contract
            "${CMAKE_CURRENT_LIST_DIR}/guest32_admission.py"
        VERBATIM)
    add_test(NAME guest32_network_admission_build COMMAND "${CMAKE_COMMAND}" --build "${PROJECT_BINARY_DIR}"
        --target heartgold_guest32_provider_closure -j8)
    set_tests_properties(guest32_network_admission_build PROPERTIES FIXTURES_SETUP guest32_network_admission)
    add_test(NAME guest32_dwc_rule_integration COMMAND "${Python3_EXECUTABLE}" -B
        "${PROJECT_SOURCE_DIR}/tests/test_guest32_dwc_rules.py" --build "${PROJECT_BINARY_DIR}"
        --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>)
    set_tests_properties(guest32_dwc_rule_integration PROPERTIES FIXTURES_REQUIRED guest32_network_admission)
    add_test(NAME guest32_network_admission_rejection COMMAND "${Python3_EXECUTABLE}" -B
        "${PROJECT_SOURCE_DIR}/tests/test_guest32_admission.py" --build "${PROJECT_BINARY_DIR}"
        --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>)
    set_tests_properties(guest32_network_admission_rejection PROPERTIES
        FIXTURES_REQUIRED guest32_network_admission FIXTURES_SETUP guest32_network_candidates)
    add_test(NAME guest32_general_rules COMMAND "${Python3_EXECUTABLE}" -B
        "${PROJECT_SOURCE_DIR}/tests/test_guest32_rules.py" --build "${PROJECT_BINARY_DIR}"
        --llvm-bin "${guest32_tools}" --lowerer $<TARGET_FILE:guest32-lower>)
    set_tests_properties(guest32_general_rules PROPERTIES FIXTURES_REQUIRED guest32_network_candidates)
endif()

# Original ARM9 Wireless Manager link-level implementation and native state.
add_library(hg_wm_arm9 SHARED
    "${PROJECT_SOURCE_DIR}/hardware_drivers/wireless/wm_arm9_provider.c")
target_compile_definitions(hg_wm_arm9 PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>")
target_include_directories(hg_wm_arm9 PRIVATE
    "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_options(hg_wm_arm9 PRIVATE
    "$<$<COMPILE_LANGUAGE:C,CXX>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>")
target_link_libraries(hg_wm_arm9 PRIVATE
    nitro_config "${overlay_link_dir}/interfaces/main.tbd")
target_link_options(hg_wm_arm9 PRIVATE
    "LINKER:-dead_strip"
    "LINKER:-exported_symbol,_WM_GetLinkLevel")
set_target_properties(hg_wm_arm9 PROPERTIES
    OUTPUT_NAME "heartgold_wm_arm9"
    LIBRARY_OUTPUT_DIRECTORY "${overlay_link_dir}"
    INSTALL_NAME_DIR "@rpath"
    BUILD_WITH_INSTALL_NAME_DIR TRUE)
add_dependencies(hg_wm_arm9
    heartgold_native_headers
    fx_constants
    heartgold_overlay_link_contract)


# Preserve every original archive and provider contract.
# Only the runtime dylib set changes in first-playable mode.
set(hg_native_image_targets)
set(hg_native_binding_args)
set(hg_native_binding_dependencies)
foreach(id IN LISTS hg_selected_overlay_ids)
    list(APPEND hg_native_image_targets heartgold_image_${id})
    set(archive ${hg_overlay_${id}_archive})
    set(anchor "${overlay_link_dir}/image_${id}.c")
    file(GENERATE OUTPUT "${anchor}" CONTENT "const unsigned HG_NativeOverlay${id}_ID = ${id};\n")
    add_library(heartgold_image_${id} SHARED "${anchor}")
    target_link_options(heartgold_image_${id} PRIVATE
        "LINKER:-force_load,$<TARGET_FILE:${archive}>" "@${overlay_link_dir}/image_${id}.rsp" "LINKER:-rpath,@loader_path")
    set_target_properties(heartgold_image_${id} PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${overlay_link_dir}"
        INSTALL_NAME_DIR "@rpath" BUILD_WITH_INSTALL_NAME_DIR TRUE
        LINK_DEPENDS "${hg_interface_outputs};$<TARGET_FILE:${archive}>")
    add_dependencies(heartgold_image_${id} heartgold_overlay_link_contract)
    if(id EQUAL 45)
        set_target_properties(heartgold_image_${id} PROPERTIES LINKER_LANGUAGE CXX)
        target_sources(heartgold_image_${id} PRIVATE
            "${CMAKE_CURRENT_LIST_DIR}/native_lobby_cpp_abi.cpp")
    endif()

    if(id EQUAL 45 OR id EQUAL 75 OR id EQUAL 80 OR id EQUAL 39 OR id EQUAL 44 OR id EQUAL 90 OR id EQUAL 91 OR id EQUAL 92 OR id EQUAL 93)
        target_link_libraries(heartgold_image_${id} PRIVATE
            hg_ovy0_wifi_subset)
    endif()
    if(id IN_LIST hg_dwc_status_consumer_ids)
        target_link_libraries(heartgold_image_${id} PRIVATE hg_dwc_status)
    endif()
    # Original OVY_70 GTS networking uses OVY_0 DWC/Wi-Fi providers.
    if(id EQUAL 70)
        target_link_libraries(heartgold_image_${id} PRIVATE
            hg_dwc_status hg_ovy0_wifi_subset)
    endif()
    # Original OVY_75 GTS server imports resolve from OVY_70.
    # Runtime overlay residency must be separately validated.
    if(id EQUAL 75)
        target_link_libraries(heartgold_image_${id} PRIVATE
            heartgold_image_70 hg_dwc_status hg_ovy0_wifi_subset)
    endif()
    # Original OVY_38 HTTP engine imports OVY_0 DWC services.
    if(id EQUAL 38)
        target_link_libraries(heartgold_image_${id} PRIVATE hg_dwc_status)
    endif()
    # OVY_72 imports original GameStats implementations from OVY_38,
    # as well as the existing OVY_0 DWC and Wi-Fi providers.
    if(id EQUAL 72)
        target_link_libraries(heartgold_image_${id} PRIVATE
            heartgold_image_38 hg_dwc_status hg_ovy0_wifi_subset)
    endif()
    # Native link closure for original WFC imports in OVY_73.
    # Runtime overlay-residency semantics require separate validation.
    if(id EQUAL 73)
        target_link_libraries(heartgold_image_${id} PRIVATE
            heartgold_image_72 hg_dwc_status)
    endif()
    if(id EQUAL 12)
        target_link_libraries(heartgold_image_12 PRIVATE hg_wm_arm9)
    endif()
    add_custom_command(TARGET heartgold_image_${id} POST_BUILD
        COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_LIST_DIR}/native_overlay_preflight.py"
            --otool "${HG_NATIVE_OTOOL}" $<TARGET_FILE:heartgold_image_${id}>
        VERBATIM)
    target_link_libraries(heartgold PRIVATE heartgold_image_${id})
    list(APPEND hg_native_binding_args --image "${id}=$<TARGET_FILE:heartgold_image_${id}>")
    list(APPEND hg_native_binding_dependencies heartgold_image_${id} "$<TARGET_FILE:heartgold_image_${id}>")
endforeach()
add_custom_command(OUTPUT "${overlay_link_dir}/bindings.inc" "${overlay_link_dir}/bindings.json"
    COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_LIST_DIR}/native_overlay_bindings.py"
        --contracts "${overlay_contracts}" ${hg_native_binding_args}
        --output "${overlay_link_dir}/bindings.inc" --report "${overlay_link_dir}/bindings.json"
    COMMAND "${CMAKE_COMMAND}" -E touch_nocreate "${overlay_link_dir}/bindings.inc"
    DEPENDS ${hg_native_binding_dependencies} "${overlay_contracts}"
        "${CMAKE_CURRENT_LIST_DIR}/native_overlay_bindings.py"
    VERBATIM)
add_custom_target(heartgold_overlay_bindings DEPENDS "${overlay_link_dir}/bindings.inc")
add_dependencies(heartgold heartgold_overlay_bindings)
set_property(TARGET heartgold APPEND PROPERTY LINK_DEPENDS "${overlay_exports}")
# Resident Nintendo DWC/WM objects also import native OVY_0 providers.
# PRIVATE overlay links do not satisfy the executable's static archives.
target_link_libraries(heartgold PRIVATE
    hg_dwc_status
    hg_wm_arm9
    hg_ovy0_wifi_subset)

target_link_options(heartgold PRIVATE "LINKER:-export_dynamic" "LINKER:-exported_symbols_list,${overlay_exports}")
target_sources(heartgold PRIVATE "${PROJECT_SOURCE_DIR}/hardware_drivers/os/game_overlays.c")
target_compile_definitions(heartgold PRIVATE HG_NATIVE_OVERLAYS)
target_include_directories(heartgold PRIVATE "${overlay_link_dir}")
add_test(NAME native_overlay_manifest COMMAND "${Python3_EXECUTABLE}" -B -m unittest discover
    -s "${PROJECT_SOURCE_DIR}/tests" -p "test_native_overlay_manifest.py")

add_custom_target(heartgold_native_images DEPENDS ${hg_native_image_targets} heartgold_overlay_bindings)
include("${CMAKE_CURRENT_LIST_DIR}/dwc_native_data.cmake")

add_test(NAME native_overlay_bindings COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_overlay_bindings.py"
    --build "${PROJECT_BINARY_DIR}" --sdk "${ntr_source}" --compiler "${CMAKE_C_COMPILER}")
add_test(NAME native_field_effect_abi COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_field_effect_abi.py" --build "${PROJECT_BINARY_DIR}")
add_test(NAME native_overlay_data COMMAND "${Python3_EXECUTABLE}" -B -m unittest discover
    -s "${PROJECT_SOURCE_DIR}/tests" -p "test_native_assembly*.py")

add_test(NAME native_dsprot_nsbta COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_dsprot_nsbta.py" --build "${PROJECT_BINARY_DIR}")
add_test(NAME native_nnsys_data COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_nnsys_native_data.py" --build "${PROJECT_BINARY_DIR}")

# OVY_39 private runtime views are checked against their actual source, not
# duplicated host declarations. Link only the real data member and SDK services.
add_custom_target(heartgold_global_terminal_data DEPENDS
    "${overlay_link_dir}/data/asm/global_terminal_data.S"
    "${overlay_link_dir}/data/asm/global_terminal_socket_data.S")
add_dependencies(heartgold_overlay_39 heartgold_global_terminal_data)
add_executable(test_global_terminal_layout "${PROJECT_SOURCE_DIR}/tests/test_global_terminal_layout.c"
    "${overlay_link_dir}/data/asm/global_terminal_socket_data.S")
add_dependencies(test_global_terminal_layout heartgold_global_terminal_data heartgold_overlay_native_sources heartgold_native_headers)
target_link_libraries(test_global_terminal_layout PRIVATE nitro_sdk)
target_include_directories(test_global_terminal_layout PRIVATE "$<TARGET_PROPERTY:heartgold_main,INCLUDE_DIRECTORIES>")
target_compile_definitions(test_global_terminal_layout PRIVATE "$<TARGET_PROPERTY:heartgold_main,COMPILE_DEFINITIONS>"
    HG_GLOBAL_TERMINAL_SOCKET_SOURCE="${native_root}/src/global_terminal/global_terminal_socket.c")
target_compile_options(test_global_terminal_layout PRIVATE
    "$<$<COMPILE_LANGUAGE:C>:$<TARGET_PROPERTY:heartgold_main,COMPILE_OPTIONS>>"
    "$<$<COMPILE_LANGUAGE:C>:-UNDEBUG;-fsanitize=address,undefined;-fno-sanitize-recover=all>")
target_link_options(test_global_terminal_layout PRIVATE -fsanitize=address,undefined -Wl,-dead_strip)
add_test(NAME global_terminal_native_layout COMMAND test_global_terminal_layout)
add_test(NAME global_terminal_native_data COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_global_terminal_native.py" --build "${PROJECT_BINARY_DIR}")
add_test(NAME global_terminal_native_images COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_global_terminal_native.py" --build "${PROJECT_BINARY_DIR}" --images)
set_tests_properties(global_terminal_native_images PROPERTIES TIMEOUT 120)

add_test(NAME global_terminal_native_image40 COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_global_terminal_native.py" --build "${PROJECT_BINARY_DIR}" --image 40)
set_tests_properties(global_terminal_native_layout PROPERTIES TIMEOUT 15)

add_custom_target(heartgold_image_report
    COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_LIST_DIR}/native_graph_report.py"
        --game "${game_source}" --build "${PROJECT_BINARY_DIR}"
        --out "${PROJECT_BINARY_DIR}/native-graph/report" --nm "${CMAKE_NM}"
    COMMENT "Inspect current native artifacts across the entire original image graph"
    VERBATIM)
add_test(NAME native_data_ir COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_data_ir.py")
add_test(NAME native_image_graph COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_image_graph.py")
set_tests_properties(native_data_ir native_image_graph PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")

add_test(NAME native_provider_registry COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_provider_registry.py")

add_test(NAME native_link_evidence COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_link_evidence.py")
add_test(NAME shared_provider_native COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_shared_provider_native.py")
set_tests_properties(shared_provider_native PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME dwc_common_native COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_dwc_common_native.py")
set_tests_properties(dwc_common_native PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME dwc_ac_contract COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_dwc_ac_contract.py")
set_tests_properties(dwc_ac_contract PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME dwc_native_extents COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_dwc_native_extents.py")
set_tests_properties(dwc_native_extents PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME native_abi COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_abi.py")
set_tests_properties(native_abi PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME dwc_backup_native COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_dwc_backup_native.py")
set_tests_properties(dwc_backup_native PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME spin_trade_native_data COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_spin_trade_data.py")
set_tests_properties(spin_trade_native_data PROPERTIES
    ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")
add_test(NAME native_follow_data COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_follow_data.py")
set_tests_properties(native_overlay_manifest native_overlay_data native_link_evidence native_follow_data
    PROPERTIES ENVIRONMENT "HEARTGOLD_TEST_BINARY_DIR=${PROJECT_BINARY_DIR}")


# HEARTGOLD_OVY45_NATIVE_ITERATOR_ABI
# Scope the original pointer-sized iterator ABI to one native C member.
# Do not modify or relax the pinned Nintendo DS header.
if(TARGET heartgold_overlay_45)
    set_property(
        SOURCE "${game_source}/src/lobby/ppw_lobby_get_work.c"
        APPEND PROPERTY COMPILE_OPTIONS
        "-include"
        "${CMAKE_SOURCE_DIR}/native-adaptations/OVY_45/tree-iterator-native.h"
    )
endif()


# HEARTGOLD_OVY45_TARGET_ITERATOR_ABI
# OVY_45-wide native representation of the original DS iterator.
# Only C/C++ translation units receive this header; assembly does not.
# The pinned upstream sources and their DS assertions are unchanged.
if(TARGET heartgold_overlay_45)
    target_compile_options(heartgold_overlay_45 PRIVATE
        "$<$<OR:$<COMPILE_LANGUAGE:C>,$<COMPILE_LANGUAGE:CXX>>:SHELL:-include ${CMAKE_SOURCE_DIR}/native-adaptations/OVY_45/tree-iterator-native.h>"
    )
endif()
