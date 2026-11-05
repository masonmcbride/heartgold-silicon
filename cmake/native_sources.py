#!/usr/bin/env python3
"""Explicit, per-file native build adaptations of the pinned original sources.

No upstream writes. Every caller supplies one input and one deterministic output;
unknown files and changed expected fragments fail instead of silently drifting.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import importlib.util

_batch_spec = importlib.util.spec_from_file_location("native_coordinated", Path(__file__).with_name("native_coordinated.py"))
coordinated = importlib.util.module_from_spec(_batch_spec)
_batch_spec.loader.exec_module(coordinated)


def replace(text, old, new, count=1):
    found = text.count(old)
    if found != count:
        raise ValueError(f"Expected {count} occurrence(s), found {found}: {old!r}")
    return text.replace(old, new)


def drop(text, declaration):
    return replace(text, declaration, "\n" * declaration.count("\n"))


def span(text, first, last):
    if text.count(first) != 1:
        raise ValueError("Changed declaration start: " + first)
    start = text.index(first)
    end = text.index(last, start) + len(last)
    return text[start:end]


def party_actions(text):
    table = span(text, "static const u32 _02101CB8[] = {", "\n};")
    entries = re.findall(r"\[(PARTY_MON_CONTEXT_MENU_[A-Z0-9_]+)\] = \(u32\)(PartyMonContextMenuAction_\w+),", table)
    if len(entries) != 30 or len({name for name, _ in entries}) != 30:
        raise ValueError("Party action table changed")
    for name, callback in entries:
        # Replace exact table entries only: Take is a prefix of TakeMail.
        table = replace(table, f"[{name}] = (u32){callback},", f"[{name}] = {name},")
    return entries, table


def callbacks(text, expected):
    """Only the NNS sound heap's native callback payloads carry pointers."""
    text, count = re.subn(r"\bu32 (data[12])\b", r"uintptr_t \1", text)
    if count != expected:
        raise ValueError("Sound callback payload declarations changed")
    return "#include <stdint.h>\n" + text


# Only these inspected declarations are replaced by native stdio/string headers.
# Calls, unrelated prototypes, and fortified macros remain untouched.
LIBC_DECLARATIONS = {
    'src/field/area_data.c': ('int sprintf(char *buf, const char *fmt, ...);',),
    'src/field/field_texture_manager.c': ('int sprintf(char *buf, const char *fmt, ...);',),
    'src/game_stats_request.c': ('extern int strncmp(const char *a, const char *b, u32 n);', 'extern int sprintf(char *dest, const char *format, ...);'),
    'src/lobby/lobby_channel_map_insert_node.cpp': ('extern "C" int printf(const char *, ...);',),
    'src/lobby/lobby_char_vector_append_fill_slow.cpp': ('extern "C" void *memset(void *p, int c, u32 n);', 'extern "C" void *memcpy(void *d, const void *s, u32 n);'),
    'src/lobby/lobby_char_vector_assign.cpp': ('void *memmove(void *, const void *, u32);',),
    'src/lobby/lobby_char_vector_init_range.cpp': ('extern "C" void *memmove(void *, const void *, unsigned);',),
    'src/lobby/lobby_chat_channel_queries.cpp': ('extern "C" unsigned long strlen(const char *);',),
    'src/lobby/lobby_chat_enter_channel.cpp': ('extern "C" unsigned long strlen(const char *);',),
    'src/lobby/lobby_event_deque_capacity.cpp': ('int printf(const char *, ...);',),
    'src/lobby/lobby_event_deque_map_copy_to_array.cpp': ('extern "C" void *memmove(void *, const void *, u32);',),
    'src/lobby/lobby_u32_vector_assign_range.cpp': ('extern "C" void *memmove(void *, const void *, u32);',),
    'src/lobby/lobby_vector_growth.cpp': ('void *memset(void *, int, unsigned);', 'void *memcpy(void *, const void *, unsigned);'),
    'src/lobby/ppw_lobby.cpp': ('int printf(const char *, ...);', 'extern "C" int strcmp(const char *, const char *);'),
    'src/lobby/ppw_lobby_leave_sub_channel.cpp': ('extern "C" int memcmp(const void *, const void *, unsigned);',),
    'src/lobby/ppw_lobby_players_set_self.cpp': ('extern "C" int memcmp(const void *, const void *, u32);',),
    'src/lobby/ppw_lobby_start_recruit.cpp': ('extern "C" char *strncpy(char *, const char *, unsigned);',),
    'src/lobby/ppw_lobby_update_my_profile.cpp': ('extern "C" int memcmp(const void *, const void *, u32);',),
    'src/stats_upload.c': ('int snprintf(char *, u32, const char *, ...);', 'int sprintf(char *, const char *, ...);', 'int strncmp(const char *, const char *, size_t);'),
    'src/wifi_connection.c': ('extern int sprintf(char *dest, const char *format, ...);',),
    'lib/NitroDWC/src/ap_connect.c': ('extern int sprintf(char *, const char *, ...);',),
    'lib/NitroDWC/src/ap_connect_control.c': ('extern int strncmp(const char *, const char *, u32);',),
    'lib/NitroDWC/src/auth_http.c': ('extern int strncmp(const char *a, const char *b, u32 n);',),
    'lib/NitroDWC/src/dwc_main.c': ('extern char *strchr(const char *s, int c);',),
    'lib/NitroDWC/src/gp_api.c': ('extern void *memset(void *, int, u32);', 'extern int strcmp(const char *, const char *);'),
    'lib/NitroDWC/src/gp_buffer.c': ('extern int sprintf(char *, const char *, ...);', 'extern int strncmp(const char *, const char *, size_t);', 'extern char *strchr(const char *, int);'),
    'lib/NitroDWC/src/gp_connect.c': ('extern int sprintf(char *, const char *, ...);', 'extern char *strstr(const char *, const char *);', 'extern int strncmp(const char *, const char *, unsigned long);'),
    'lib/NitroDWC/src/gp_main.c': ('extern char *strstr(const char *, const char *);', 'extern int strncmp(const char *, const char *, size_t);'),
    'lib/NitroDWC/src/gp_operation.c': ('extern int sprintf(char *, const char *, ...);',),
    'lib/NitroDWC/src/gp_peer.c': ('extern int strncmp(const char *, const char *, unsigned);', 'extern int sprintf(char *, const char *, ...);', 'extern char *strstr(const char *, const char *);'),
    'lib/NitroDWC/src/gp_search.c': ('extern int strcmp(const char *, const char *);', 'extern char *strstr(const char *, const char *);', 'extern char *strcpy(char *, const char *);', 'extern void *memset(void *, int, u32);'),
    'lib/NitroDWC/src/gp_utility.c': ('extern int sprintf(char *, const char *, ...);', 'extern int strncmp(const char *, const char *, size_t);', 'extern int sscanf(const char *, const char *, ...);'),
    'lib/NitroDWC/src/gs_platform.c': ('extern void *memcpy(void *, const void *, u32);', 'extern void *memmove(void *, const void *, u32);', 'extern int sprintf(char *, const char *, ...);', 'extern void *memset(void *, int, u32);', 'extern int strcmp(const char *, const char *);'),
    'lib/NitroDWC/src/gt_connection.c': ('extern int sprintf(char *, const char *, ...);', 'extern char *strchr(const char *, int);'),
    'lib/NitroDWC/src/gt_socket.c': ('extern void *memcpy(void *, const void *, u32);', 'extern int memcmp(const void *, const void *, u32);'),
    'lib/NitroDWC/src/match_browse.c': ('extern int memcmp(const void *, const void *, u32);', 'extern int strncmp(const char *, const char *, u32);'),
    'lib/NitroDWC/src/match_command.c': ('extern char *strchr(const char *s, int c);',),
    'lib/NitroDWC/src/match_connect.c': ('extern int memcmp(const void *, const void *, u32);',),
    'lib/NitroDWC/src/nat_negotiate.c': ('extern int snprintf(char *, unsigned int, const char *, ...);', 'extern int sprintf(char *, const char *, ...);'),
    'lib/NitroDWC/src/net_common.c': ('extern int strncmp(const char *, const char *, u32);', 'extern char *strchr(const char *, int);'),
    'lib/NitroDWC/src/persist_data.c': ('extern int sprintf(char *, const char *, ...);', 'extern int strncmp(const char *, const char *, size_t);'),
    'lib/NitroDWC/src/query_report_init.c': ('int sprintf(char *, const char *, ...);',),
    'lib/NitroDWC/src/sb_server.c': ('extern int sprintf(char *buf, const char *fmt, ...);',),
    'lib/NitroDWC/src/sb_serverlist.c': ('extern int strncmp(const char *a, const char *b, u32 n);', 'extern int sprintf(char *buf, const char *fmt, ...);'),
    'lib/NitroDWC/src/server_report.c': ('extern int sprintf(char *buf, const char *fmt, ...);', 'extern int sscanf(const char *str, const char *fmt, ...);'),
    'lib/NitroDWC/src/transport.c': ('extern int memcmp(const void *, const void *, u32);', 'extern char *strncpy(char *, const char *, u32);'),
    'lib/include/dwc/chat_internal.h': ('char *strchr(const char *str, int c);', 'int sprintf(char *buf, const char *fmt, ...);', 'int vsprintf(char *buf, const char *fmt, va_list args);'),
    'lib/include/dwc/http_internal.h': ('char *strchr(const char *str, int c);', 'int strncmp(const char *a, const char *b, size_t n);', 'int sprintf(char *buf, const char *fmt, ...);', 'int sscanf(const char *str, const char *fmt, ...);', 'int fseek(void *file, long offset, int whence);', 'long ftell(void *file);', 'void rewind(void *file);', 'int fclose(void *file);', 'unsigned fread(void *buf, unsigned size, unsigned count, void *file);'),
}
# Native formatting owns size_t capacities and the host va_list ABI.
# Only these redundant DS declarations are removed; calls remain unchanged.
PRINTF_DECLARATIONS = {
    "lib/NitroDWC/src/net_common.c": ("extern int OS_SNPrintf(char *, u32, const char *, ...);",),
    "lib/include/nitro/os/printf.h": (
        "int OS_SNPrintf(char * dest, u32 len, const char * format, ...);",
        "int OS_VSNPrintf(char * dest, u32 len, const char * format, va_list va);"),
}

# Exact original declarations; all callers use the SDK's two-argument comparator.
QSORT_DECLARATIONS = {
    "src/pokeathlon/pokeathlon_circle_push.c": "void MATH_QSort(void *head, u32 num, u32 width, int (*compare)(const void *, const void *), void *stackBuffer);",
    "src/pokeathlon/pokeathlon_course_ceremony.c": "void MATH_QSort(void *head, u32 num, u32 width, int (*compare)(const void *, const void *), void *stackBuffer);",
    "src/pokeathlon/pokeathlon_disc_catch.c": "void MATH_QSort(void *head, u32 num, u32 size, s32 (*compare)(const void *, const void *), void *work);",
    "src/pokeathlon/pokeathlon_goal_roll_display.c": "void MATH_QSort(void *base, u32 count, u32 width, int (*compare)(const void *, const void *), void *context);",
    "src/pokeathlon/pokeathlon_ring_drop_display.c": "void MATH_QSort(void *base, u32 count, u32 width, int (*compare)(const void *, const void *), void *context);",
    "src/pokeathlon/pokeathlon_snow_throw.c": "void MATH_QSort(void *base, u32 count, u32 width, int (*compare)(const void *, const void *), void *context);",
    "src/application/pokewalker/pokewalker_event_log.c": "void MATH_QSort(void *base, u32 count, u32 width, int (*compare)(const void *, const void *, void *), void *context);",
}

# Header declarations contradict private definitions in their owning C files.
# Each record has an exact header prototype and local forward state:
# existing = retain it; needed = insert it; none = definition precedes all uses.
PRIVATE_FUNCTIONS = {
    'src/berry_pots_app_tasks.c': ('include/berry_pots_app_internal.h', (
        ('void BerryPotsApp_StartGrowthAnims(BerryPotsAppData *data);', 'needed'),
        ('u32 BerryPotsApp_SelectPotAction(BerryPotsAppData *data, u32 selection);', 'none'),
        ('u32 BerryPotsApp_HandleSelectPotKeys(BerryPotsAppData *data);', 'needed'),
        ('u32 BerryPotsApp_HandleSelectPotTouch(BerryPotsAppData *data, BOOL *touched);', 'needed'),
        ('BOOL BerryPotsApp_HandleWateringKeys(BerryPotsAppData *data);', 'needed'),
        ('BOOL BerryPotsApp_HandleWateringTouch(BerryPotsAppData *data, BOOL *touched);', 'needed'),
        ('int BerryPotsApp_GetTouchedPot(BerryPotsAppData *data);', 'needed'),
        ('int BerryPotsApp_GetSelectPotTouch(BerryPotsAppData *data);', 'needed'),
        ('u32 BerryPotsApp_GetPotMenuState(BerryPotsAppData *data);', 'needed'),
    )),
    'src/nintendo_wfc_connect_unused_session.c': ('include/nintendo_wfc_connect_unused.h', (
        ('enum NintendoWfcMainState NintendoWfcUnused_AskConnect(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_HandleConnectChoice(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_AskLogOut(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_HandleLogOutChoice(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_StartConnect(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_WaitConnect(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_StartAuth(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_WaitAuth(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_InitHttp(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_RequestInfo(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_WaitInfo(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_RequestSetProfile(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_WaitSetProfile(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_RequestRoomCount(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_WaitRoomCount(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_AskChallengeRoom(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_StartChallengeRoomInput(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_HandleChallengeRoomInput(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_PrintReceivingTrainers(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_PrintRoomUnavailable(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_RequestTrainersDownload(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_WaitTrainersDownload(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_PrintTrainersReceived(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_PrintSendingRecord(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_RequestUpload(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_WaitUpload(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_PrintRecordSent(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_AskLeadersRank(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_StartLeadersRankInput(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_HandleLeadersRankInput(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_AskLeadersRoom(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_StartLeadersRoomInput(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_HandleLeadersRoomInput(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_PrintReceivingLeaders(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_RequestLeadersDownload(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_WaitLeadersDownload(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_PrintLeadersReceived(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_StartDisconnect(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_StartSave(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_Save(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_AskCancelChallenge(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_HandleCancelChallengeChoice(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_AskCancelDownload(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_HandleCancelDownloadChoice(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_PrintDisconnecting(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_CloseConnection(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_PrintDisconnected(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_UnusedState_Idle(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_StartExit(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_UnusedState_HandleYesNo(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_ShowHttpError(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_Disconnect(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_WaitMessage(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_WaitMessageAndDelay(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_OpenYesNoPrompt(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_ShowDwcError(NintendoWfcUnused *wfc);', 'existing'),
        ('enum NintendoWfcMainState NintendoWfcUnused_WaitErrorDismiss(NintendoWfcUnused *wfc);', 'existing'),
    )),
    'src/wifi_plaza/wifi_plaza_history.c': ('include/wifi_plaza/wifi_plaza_internal.h', (
        ('u8 WiFiPlazaHistory_RemoveOldest(WiFiPlazaHistory *history);', 'existing'),
        ('void WiFiPlazaHistory_UpdateChecksum(WiFiPlazaHistory *history);', 'existing'),
        ('void WiFiPlazaHistory_CheckChecksum(WiFiPlazaHistory *history);', 'existing'),
    )),
    'src/wifi_plaza/wifi_plaza_news.c': ('include/wifi_plaza/wifi_plaza_internal.h', (
        ('void WiFiPlazaNewsSlots_Set(WiFiPlazaNewsSlots *slots, int slot, int state, int flags);', 'existing'),
        ('void WiFiPlazaNewsSlots_AddPlayer(WiFiPlazaNewsSlots *slots, int slot, int state, int flags);', 'existing'),
        ('void WiFiPlazaNewsSlots_RemovePlayer(WiFiPlazaNewsSlots *slots, int slot);', 'existing'),
        ('void WiFiPlazaNewsSlots_SetFlags(WiFiPlazaNewsSlots *slots, int slot, int flags);', 'existing'),
        ('void WiFiPlazaNewsSlots_SetLastJoined(WiFiPlazaNewsSlots *slots, int slot);', 'existing'),
        ('BOOL WiFiPlazaNewsSlots_IsOccupied(WiFiPlazaNewsSlots *slots, int slot);', 'existing'),
        ('int WiFiPlazaNewsSlots_GetGender(WiFiPlazaNewsSlots *slots, int slot);', 'existing'),
        ('BOOL WiFiPlazaNewsSlots_IsOwn(WiFiPlazaNewsSlots *slots, int slot);', 'existing'),
        ('BOOL WiFiPlazaNewsSlots_IsOldest(WiFiPlazaNewsSlots *slots, int slot);', 'existing'),
        ('int WiFiPlazaNewsSlots_GetFlags(WiFiPlazaNewsSlots *slots, int slot);', 'existing'),
        ('u16 WiFiPlazaNewsSlots_GetChange(WiFiPlazaNewsSlots *slots);', 'existing'),
        ('BOOL WiFiPlazaNewsSlots_IsLastJoined(WiFiPlazaNewsSlots *slots, u32 slot);', 'existing'),
        ('void WiFiPlazaNewsEventList_RemoveFirst(WiFiPlazaNewsEventList *list);', 'existing'),
        ('WiFiPlazaNewsEvent *WiFiPlazaNewsEventList_GetFreeEvent(WiFiPlazaNewsEventList *list, u16 rank);', 'existing'),
        ('void WiFiPlazaNewsEvent_InsertAfter(WiFiPlazaNewsEvent *at, WiFiPlazaNewsEvent *event);', 'existing'),
        ('void WiFiPlazaNewsEventList_Insert(WiFiPlazaNewsEventList *list, WiFiPlazaNewsEvent *event);', 'existing'),
        ('void WiFiPlazaNewsEventList_Remove(WiFiPlazaNewsEventList *list, WiFiPlazaNewsEvent *event);', 'existing'),
        ('void WiFiPlazaNewsEvent_Set(WiFiPlazaNewsEvent *event, u32 a, u32 b, u32 c, const PlayerProfile *player0, const PlayerProfile *player1, const PlayerProfile *player2, const PlayerProfile *player3, u16 slot0, u16 slot1, u16 slot2, u16 slot3, u32 timer, u32 rank, u32 type);', 'existing'),
        ('BOOL WiFiPlazaNewsEvent_FormatChat(WiFiPlazaNewsEvent *event, const u8 *flags, MessageFormat *format, MsgData *msgData, String *out, enum HeapID heapID);', 'existing'),
        ('BOOL WiFiPlazaNewsEvent_FormatTapToyTrade(WiFiPlazaNewsEvent *event, const u8 *flags, MessageFormat *format, MsgData *msgData, String *out, enum HeapID heapID);', 'existing'),
        ('BOOL WiFiPlazaNewsEvent_FormatMinigameEntry(WiFiPlazaNewsEvent *event, const u8 *flags, MessageFormat *format, MsgData *msgData, String *out, enum HeapID heapID);', 'existing'),
        ('BOOL WiFiPlazaNewsEvent_FormatFootprintStamp(WiFiPlazaNewsEvent *event, const u8 *flags, MessageFormat *format, MsgData *msgData, String *out, enum HeapID heapID);', 'existing'),
        ('BOOL WiFiPlazaNewsEvent_FormatChecking(WiFiPlazaNewsEvent *event, const u8 *flags, MessageFormat *format, MsgData *msgData, String *out, enum HeapID heapID);', 'existing'),
        ('BOOL WiFiPlazaNewsEvent_FormatLobbyEventNotice(WiFiPlazaNewsEvent *event, const u8 *flags, MessageFormat *format, MsgData *msgData, String *out, enum HeapID heapID);', 'existing'),
        ('BOOL WiFiPlazaNewsEvent_FormatSpecialVisitor(WiFiPlazaNewsEvent *event, const u8 *flags, MessageFormat *format, MsgData *msgData, String *out, enum HeapID heapID);', 'existing'),
        ('BOOL WiFiPlazaNewsEvent_FormatMinigameResult(WiFiPlazaNewsEvent *event, const u8 *flags, MessageFormat *format, MsgData *msgData, String *out, enum HeapID heapID);', 'existing'),
        ('u16 WiFiPlazaNewsEvent_GetChatSlot(WiFiPlazaNewsEvent *event, u32 index);', 'existing'),
        ('u16 WiFiPlazaNewsEvent_GetTapToyTradeSlot(WiFiPlazaNewsEvent *event, u32 index);', 'existing'),
        ('u16 WiFiPlazaNewsEvent_GetMinigameEntrySlot(WiFiPlazaNewsEvent *event, u32 index);', 'existing'),
        ('u16 WiFiPlazaNewsEvent_GetFootprintStampSlot(WiFiPlazaNewsEvent *event, u32 index);', 'existing'),
        ('u16 WiFiPlazaNewsEvent_GetCheckingSlot(WiFiPlazaNewsEvent *event, u32 index);', 'existing'),
        ('u16 WiFiPlazaNewsEvent_GetLobbyEventNoticeSlot(WiFiPlazaNewsEvent *event, u32 index);', 'existing'),
        ('u16 WiFiPlazaNewsEvent_GetSpecialVisitorSlot(WiFiPlazaNewsEvent *event, u32 index);', 'existing'),
    )),
    'src/wifi_plaza/wifi_plaza_time_zone.c': ('include/wifi_plaza/wifi_plaza_internal.h', (
        ('void WiFiPlaza_GetLongitude(NARC *narc, enum HeapID heapID, int country, u16 region, s32 *longitude);', 'existing'),
    )),
}


def private_declarations(relative, text):
    """Remove allowlisted redundant exports; retain each original static body."""
    if relative in PRIVATE_FUNCTIONS:
        header, declarations = PRIVATE_FUNCTIONS[relative]
        include = '#include "' + header.removeprefix("include/") + '"'
        if text.count(include) != 1:
            raise ValueError("Private function include changed: " + relative)
        forwards = []
        for prototype, state in declarations:
            definition = "static " + prototype[:-1] + " {"
            forward = "static " + prototype
            if (state not in ("existing", "needed", "none")
                    or text.count(definition) != 1
                    or text.count(forward) != int(state == "existing")):
                raise ValueError("Private function ownership changed: " + prototype)
            if state != "existing":
                name = re.search(r"\b(\w+)\(", prototype)[1]
                used_before = re.search(r"\b" + re.escape(name) + r"\b", text).start() < text.index(definition)
                if used_before != (state == "needed"):
                    raise ValueError("Private function forward requirement changed: " + prototype)
            if state == "needed":
                forwards.append(forward)
        if forwards:
            text = replace(text, include, include + "\n\n" + "\n".join(forwards))
        return text
    for header, declarations in PRIVATE_FUNCTIONS.values():
        if relative == header:
            for prototype, _ in declarations:
                text = drop(text, prototype)
    return text


# Native emission of the original per-overlay static initializer arrays.
SINIT_CALLBACKS = {
    "src/application/ball_capsule_editor.c": "BallCapsuleEditor_LoadBattleOverlays",
    "src/battle/battle_main.c": "Battle_StaticInit",
}
# Explicit calls to ARM compiler arithmetic helpers become native compiler operations.
# Both signed divisors are positive constants; no divide-by-zero/overflow ABI changes.
COMPILER_OPERATIONS = {
    'src/pokeathlon/pokeathlon_hurdle_dash_race.c': ('a8f58df23bea1c02735274dd2d9a2cb1ad9018a54143b82416260229df609590', 's32 _s32_div_f(s32 num, s32 den);', '_s32_div_f((u8)(frames % 30) * 100, 30)', '(((u8)(frames % 30) * 100) / 30)'),
    'src/pokeathlon/pokeathlon_disc_catch.c': ('9c0908e9995aa5ac37ca4080449397e6e5d80eeba68ac01e3c3a4ec2e6650571', 's32 _s32_div_f(s32 dividend, s32 divisor);', '_s32_div_f(38 * (progress * (path - 7)), 1000)', '((38 * (progress * (path - 7))) / 1000)'),
    'src/pokeathlon/pokeathlon_relay_run.c': ('67b56bd002b5b409d950d7a4d43954710847425a5b067e7b923eb4c0a42400cd', 'f32 _fflt(int value);', '_fflt(VEC_Mag(&work.flick) / FX32_ONE)', '((f32)(VEC_Mag(&work.flick) / FX32_ONE))'),
}

# Direct native representations of original ARM register operations.
ARM_INLINE_OPERATIONS = {
    'lib/libCPS/src/cps_bignum.c': ('32e9d64dce1461277bab736ae11b05790907d49af90d8ac71d8cf7e118ddebb8', [('asm u64 get48bits_2(const u16 *top) {\n    ldrh r1, [r0]\n    ldrh r0, [r0, #-2]\n    mov r0, r0, lsl #0x10\n    bx lr\n}', 'u64 get48bits_2(const u16 *top) {\n    return ((u64)top[0] << 32) | ((u64)top[-1] << 16);\n}'), ('asm u64 get48bits_3(const u16 *top) {\n    ldrh r1, [r0]\n    ldrh r2, [r0, #-2]\n    ldrh r3, [r0, #-4]\n    orr r0, r3, r2, lsl #16\n    bx lr\n}', 'u64 get48bits_3(const u16 *top) {\n    return ((u64)top[0] << 32) | ((u64)top[-1] << 16) | top[-2];\n}'), ('asm u64 get64bits(const u16 *top) {\n    ldrh r2, [r0]\n    ldrh r3, [r0, #-2]\n    orr r1, r3, r2, lsl #16\n    ldrh r2, [r0, #-4]\n    ldrh r3, [r0, #-6]\n    orr r0, r3, r2, lsl #16\n    bx lr\n}', 'u64 get64bits(const u16 *top) {\n    return ((u64)top[0] << 48) | ((u64)top[-1] << 32) | ((u64)top[-2] << 16) | top[-3];\n}'), ('u32 product = b * a[i] + carry;', 'u32 product = (u32)b * a[i] + carry;'), ('square = a[i] * a[i];', 'square = (u32)a[i] * a[i];')]),
    'lib/NitroWiFi/src/wcm_control.c': ('764aadf1be3bda8a676dd66980180f6cfb016a759e7627a25525c29b85ae0b80', [('asm u32 WcmCountBits(u32 value) {\n    mov r1, r0\n    mov r0, #0\n    mov r3, #1\n@loop:\n    clz r2, r1\n    rsbs r2, r2, #0x1f\n    bcc @done\n    b @clear\n@done:\n    bx lr\n@clear:\n    bic r1, r1, r3, lsl r2\n    add r0, r0, #1\n    b @loop\n}', 'u32 WcmCountBits(u32 value) {\n    return (u32)__builtin_popcount(value);\n}'), ('asm u32 WcmCountLeadingZero(u32 value) {\n    clz r0, r0\n    bx lr\n}', 'u32 WcmCountLeadingZero(u32 value) {\n    return value ? (u32)__builtin_clz(value) : 32;\n}')]),
}

# Bounded explicit soft-float calls: positive exact integers plus 0.5, then truncation.
# Both long-multiply operands originate as s32, so their product fits s64.
COMPILER_BOUNDED_OPERATIONS = {
    'src/wifi_plaza/wifi_plaza_instrument.c': ('a76f3608ced824d35d9e7492edf5f19be44d8577e362ebb505f160beeae9e507', [('s64 _ll_mul(s64 a, s64 b);', '', 1), ('u32 _fflt(s32 value);', '', 1), ('u32 _fadd(u32 a, u32 b);', '', 1), ('s32 _ffix(u32 value);', '', 1), ('_ll_mul((s64)(s32)(frame > 0 ? (float)(frame << 12) + 0.5f : (float)(frame << 12) - 0.5f), (s64)delta)', '(((s64)(s32)(frame > 0 ? (float)((s32)((u32)frame << 12)) + 0.5f : (float)((s32)((u32)frame << 12)) - 0.5f)) * (s64)delta)', 3), ('    u32 y;\n    u32 x;', '    f32 y;\n    f32 x;', 2), ('_fadd(0x3F000000, _fflt(11 << 14))', '(0.5f + (f32)(11 << 14))', 4), ('_fadd(0x3F000000, _fflt(14 << 12))', '(0.5f + (f32)(14 << 12))', 4), ('_fadd(0x3F000000, _fflt(14 << 14))', '(0.5f + (f32)(14 << 14))', 4), ('_fadd(0x3F000000, _fflt(15 << 14))', '(0.5f + (f32)(15 << 14))', 2), ('_fadd(0x3F000000, _fflt(2 << 12))', '(0.5f + (f32)(2 << 12))', 4), ('_fadd(0x3F000000, _fflt(2 << 14))', '(0.5f + (f32)(2 << 14))', 4), ('_fadd(0x3F000000, _fflt(3 << 16))', '(0.5f + (f32)(3 << 16))', 2), ('_ffix(x)', '((s32)x)', 12), ('_ffix(y)', '((s32)y)', 12), ('tween->duration << 12', '(s32)((u32)tween->duration << 12)', 6)]),
}

# Source-guarded lowering of original ARM compiler arithmetic helpers.
# Preserve low-64-bit multiplication and signed integer-to-f32 conversion.
COMPILER_BOUNDED_OPERATIONS.update({'src/application/footprint_stamp_effects.c': ('aa6a4cadb2188647e22a671363806fcd10f6b29959c0abe6ba08c1b73f852f35', [('_ll_mul((s64)scaleX * 100 / FX32_ONE, length)', '((s64)((u64)((s64)scaleX * 100 / FX32_ONE) * (u64)(s64)length))', 1), ('_ll_mul((s64)scaleY * 100 / FX32_ONE, length)', '((s64)((u64)((s64)scaleY * 100 / FX32_ONE) * (u64)(s64)length))', 1)]), 'src/application/plaza_game_mime_jr_top.c': ('83ec77662a263f8b8731a1ce6d2b9de13648b6e07ca5cc3bc274a9cc4c334dfc', [('_f_lltof(sinValue)', '((f32)sinValue)', 2), ('_f_lltof(cosValue)', '((f32)cosValue)', 2)])})

COMPILER_NATIVE_SOURCES = tuple(COMPILER_BOUNDED_OPERATIONS) + tuple(SINIT_CALLBACKS) + tuple(COMPILER_OPERATIONS) + tuple(ARM_INLINE_OPERATIONS) + (
    "src/application/pokedex/pokedex_main_seq.c", "src/field/weather_manager.c")


OVERLAY_NATIVE_SOURCES = ("src/global_terminal/global_terminal_socket.c",) + tuple(path for path in LIBC_DECLARATIONS if not path.endswith(".h")) + ("src/wifi_setup/wifi_setup_share.c",) + tuple(QSORT_DECLARATIONS) + ("lib/NitroDWC/src/http_engine_request.c", "src/voice_chat.c", "lib/libVCT/src/vct_packet_buffer.c") + tuple(PRIVATE_FUNCTIONS) + COMPILER_NATIVE_SOURCES
OVERLAY_NATIVE_SOURCES = tuple(dict.fromkeys(OVERLAY_NATIVE_SOURCES + tuple(p for p in coordinated.SOURCES if not p.endswith(".h"))))

OVERLAY_NATIVE_SOURCES = tuple(dict.fromkeys(OVERLAY_NATIVE_SOURCES + tuple(p for p in coordinated.HEADER_ROUTES if not p.endswith(".h"))))
OVERLAY_NATIVE_SOURCES = tuple(dict.fromkeys(OVERLAY_NATIVE_SOURCES + ("src/application/ball_capsule_editor.c",)))

OVERLAY_NATIVE_SOURCES = tuple(dict.fromkeys(OVERLAY_NATIVE_SOURCES + ("lib/libVCT/src/vct_audio_send.c",)))

def native_libc(relative, text):
    for declaration in LIBC_DECLARATIONS[relative]:
        text = drop(text, declaration)
    if relative == "src/lobby/ppw_lobby.cpp":
        text = replace(text, "using std::va_list;", "using ::va_list;")
    headers = '#include <stdio.h>\n#include <string.h>\n'
    if relative == "src/lobby/ppw_lobby.cpp":
        headers += '#include <cstring>\n'
    return headers + text



POKEWALKER_ABI_INPUTS = {
    "include/application/pokewalker/pokewalker_ir.h": "436e1dd6795cfbf8ecf4b5a65ad81107299c308270ee167800166e3d2836d765",
    "include/application/pokewalker/pokewalker_ir_internal.h": "6a0ec0b5ef36c2d20798b04d86ec1166c83cb56c95fd3824f26dfdd424a77101",
    "src/application/pokewalker/pokewalker_ir_requests.c": "053ab4bdeff6fc289e70c3fdb511f827613c11cd3a97dbbd88dc1908c438bb89",
    "src/application/pokewalker/pokewalker_ir_status.c": "caf8d128e91464e5c48d26d4681a1e3b9ec5ab70c3d98407e15f4b663c7cbc70",
    "lib/include/nitro/card/card_spi_wait_internal.h": "7bc527d7f68f14131ba83db63dd661d33032449ece97658cfff6ef26fa0648bb",
    "lib/NitroSDK/src/card/card_spi_wait.c": "14a2c756126316176209128569cc9f6e5987c8d225068cbcf1c3d14949829a33",
    "lib/NitroSDK/src/card/card_spi_wait_cycles.c": "65d6cf1f16ad44ca93bfb79fe452ef645fe0ed2e0b34ea905fdd198ffdd998b8",
    "lib/NitroSDK/src/card/card_spi_wait_init.c": "2dbdf695362a0c97a30246a56a7109f63e05a96774887678c45e1f8b574c7126"
}


def pokewalker_abi(relative, text, root):
    if hashlib.sha256(text.encode()).hexdigest() != POKEWALKER_ABI_INPUTS[relative]:
        raise ValueError('Pokewalker native ABI source drift: '+relative)
    internal = 'include/application/pokewalker/pokewalker_ir_internal.h'
    requests = 'src/application/pokewalker/pokewalker_ir_requests.c'
    if relative == 'include/application/pokewalker/pokewalker_ir.h':
        return '#include <stdint.h>\n'+replace(text,'void *data, u32 address, int size','void *data, uintptr_t address, int size')
    if relative == internal:
        original_requests=(root/requests).read_text()
        if hashlib.sha256(original_requests.encode()).hexdigest()!=POKEWALKER_ABI_INPUTS[requests]:
            raise ValueError('Pokewalker shared owner changed')
        buffers=span(original_requests,'typedef struct PokewalkerIrWorkBuffers {','} PokewalkerIrWorkBuffers;')
        sync=span(original_requests,'typedef struct PokewalkerIrWorkSync {','} PokewalkerIrWorkSync;')
        progress=span(original_requests,'typedef struct PokewalkerIrWorkProgress {','} PokewalkerIrWorkProgress;')
        transfer=span(text,'typedef struct PokewalkerIrTransfer {','} PokewalkerIrTransfer;')
        # The transfer alias starts one original pointer into the queue. Its
        # opaque prefix is the rest of that same queue, not extra storage.
        transfer=replace(transfer,'u8 unk_00[0x1C];','u8 unk_00[sizeof(OSMessageQueue) - sizeof(void *)];')
        transfer=replace(transfer,'u32 address;', 'uintptr_t address;')
        transfer=replace(transfer,'u32 addressStart;', 'uintptr_t addressStart;')
        old=span(text,'typedef struct PokewalkerIrTransfer {','} PokewalkerIrTransfer;')
        text=replace(text,old,transfer)
        # The full original work view already covers header and buffer owners.
        # Its unk_1C is the one-message array, an OSMessage (native pointer).
        text=replace(text,'u32 unk_1C;','OSMessage messages[1];')
        text=replace(text,'    void *compressedStroll;\n} PokewalkerIrWork;',
                     '    void *compressedStroll;\n    u8 *compressedRecordSizes;\n    u8 *compressedRecords;\n} PokewalkerIrWork;')
        # One canonical mutex/queue/payload allocation replaces separate C
        # declarations whose original aliases span owner boundaries.
        payload=transfer.split('u8 command;',1)[1].split('} PokewalkerIrTransfer;',1)[0]
        payload='    u8 command;'+payload
        sync=sync[:sync.index('    u8 command;')]+payload+'    u16 unk_3E;\n    u8 buffer[0x74];\n} PokewalkerIrWorkSync;'
        text=replace(text,'extern OSMessage gPokewalkerIrBuffers[];',
                     'extern PokewalkerIrWorkBuffers gPokewalkerIrBuffers;')
        text=replace(text,'extern OSMutex gPokewalkerIrSync;',
                     'extern PokewalkerIrWorkSync gPokewalkerIrSync;\nextern PokewalkerIrWorkProgress gPokewalkerIrProgress;')
        text=replace(text,'extern PokewalkerIrWork gPokewalkerIrWork;',
                     buffers+'\n'+sync+'\n'+progress+'\nextern PokewalkerIrWork gPokewalkerIrWork;')
        return '#include <stdint.h>\n'+text
    if relative == requests:
        text=replace(text,'#include "application/pokewalker/pokewalker_ir.h"',
                     '#include "application/pokewalker/pokewalker_ir_internal.h"')
        text=replace(text,span(text,'typedef struct PokewalkerIrWorkHeader {','PokewalkerIrWorkProgress gPokewalkerIrProgress;'),
                     'PokewalkerIrWork gPokewalkerIrWork;\nPokewalkerIrWorkSync gPokewalkerIrSync;')
        text=text.replace('gPokewalkerIrBuffers.', 'gPokewalkerIrWork.').replace('gPokewalkerIrProgress.', 'gPokewalkerIrSync.')
        text=replace(text,'gPokewalkerIrWork.status = status;', 'gPokewalkerIrWork.status = (PokewalkerIrStatus *)status;',count=2)
        text=replace(text,'gPokewalkerIrWork.blocks = blocks;', 'gPokewalkerIrWork.blocks = (PokewalkerIrBlocks *)blocks;',count=2)
        text += pokewalker_aliases(root)
        return text
    if relative.endswith('/pokewalker_ir_status.c'):
        return text.replace('gPokewalkerIrTransfer.', 'gPokewalkerIrSync.')
    if relative.endswith('/card_spi_wait_internal.h'):
        # Materialize the original interior alias as an actual C subobject,
        # so optimized native code never accesses incompatible global views.
        first=text.index('    u32 active;      //')
        last=text.index('    u32 unk_10;',first)+len('    u32 unk_10;')
        return text[:first]+'    CardSpiTransfer transfer;'+text[last:]
    if relative.endswith('/card_spi_wait_init.c'):
        text=replace(text,'    u32 active;', '    _Alignas(8) u32 active;')
        text=replace(text,'extern CardSpiWaitHead gCardSpiWait;', 'extern CardSpiWait gCardSpiWait;')
        text=replace(text,'gCardSpiWait.active', 'gCardSpiWait.transfer.active')
        return text+'\n_Static_assert(__builtin_offsetof(CardSpiWaitHead,active) == __builtin_offsetof(CardSpiWait,transfer.active), "shared SPI head");\n'
    if relative.endswith('/card_spi_wait.c'):
        # Lvalue macros preserve the original read/write and polling order.
        # With no physical cartridge transport, the accessor terminates before
        # dereferencing an unmapped DS address or returning invented status.
        text=replace(text,'#pragma force_active on', '#include \"card_spi_host.h\"\n#pragma force_active on')
        text=text.replace('gCardSpiWait.input','gCardSpiWait.transfer.input').replace('gCardSpiWait.output','gCardSpiWait.transfer.output')
        return text.replace('&gCardSpiTransfer','&gCardSpiWait.transfer')
    return text


def pokewalker_aliases(root):
    alias_map=root/'src/application/pokewalker/pokewalker_ir_requests.alias-map.json'
    if hashlib.sha256(alias_map.read_bytes()).hexdigest() != '7ac91219180952f182d6be01bae10ad1e5de9dca68a4504020da05007148a766':
        raise ValueError('Pokewalker original shared-storage aliases changed')
    internal=(root/'include/application/pokewalker/pokewalker_ir_internal.h').read_text()
    transfer=span(internal,'typedef struct PokewalkerIrTransfer {','} PokewalkerIrTransfer;')
    fields=re.findall(r'\b(?:u8|u16|u32)\s*\*?\s*(\w+)\s*(?:;|\[)',transfer)
    fields=[f for f in fields if f!='unk_00']
    aliases={
        'gPokewalkerIrBuffers':('gPokewalkerIrWork','__builtin_offsetof(PokewalkerIrWork,messages)'),
        'gPokewalkerIrImageSizes':('gPokewalkerIrWork','__builtin_offsetof(PokewalkerIrWork,compressedImageSizes)'),
        'gPokewalkerIrStrollSizes':('gPokewalkerIrWork','__builtin_offsetof(PokewalkerIrWork,compressedStrollSizes)'),
        'gPokewalkerIrMessageQueue':('gPokewalkerIrSync','__builtin_offsetof(PokewalkerIrWorkSync,queue)'),
        'gPokewalkerIrTransfer':('gPokewalkerIrSync','__builtin_offsetof(PokewalkerIrWorkSync,queue)+sizeof(void*)'),
        'gPokewalkerIrProgress':('gPokewalkerIrSync','__builtin_offsetof(PokewalkerIrWorkSync,totalChunks)'),
        'gPokewalkerIrSendBuffer':('gPokewalkerIrSync','__builtin_offsetof(PokewalkerIrWorkSync,buffer)'),
    }
    out='\n__attribute__((used)) static void hg_pokewalker_storage_aliases(void) {\n'
    for name,(owner,offset) in aliases.items():
        out+='    __asm__ volatile(".globl _'+name+'\\n.set _'+name+',_'+owner+'+%c0" : : "i"('+offset+'));\n'
    out+='}\n'
    def assertion(expr):return '_Static_assert('+expr+', "Pokewalker shared storage ABI");\n'
    requests=(root/'src/application/pokewalker/pokewalker_ir_requests.c').read_text()
    buffers=span(requests,'typedef struct PokewalkerIrWorkBuffers {','} PokewalkerIrWorkBuffers;')
    names=re.findall(r'\b(?:OSMessage|PokewalkerIrIdentity|void|u8|u64)\s*\*?\s*(\w+)\s*(?:;|\[)',buffers)
    for field in names:
        out+=assertion('__builtin_offsetof(PokewalkerIrWork,'+field+') == __builtin_offsetof(PokewalkerIrWork,messages)+__builtin_offsetof(PokewalkerIrWorkBuffers,'+field+')')
    for field in fields:
        out+=assertion('__builtin_offsetof(PokewalkerIrWorkSync,'+field+') == __builtin_offsetof(PokewalkerIrWorkSync,queue)+sizeof(void*)+__builtin_offsetof(PokewalkerIrTransfer,'+field+')')
    for field in ['totalChunks','totalChunk','totalSize','unk_3E','buffer']:
        out+=assertion('__builtin_offsetof(PokewalkerIrWorkSync,'+field+') == __builtin_offsetof(PokewalkerIrWorkSync,totalChunks)+__builtin_offsetof(PokewalkerIrWorkProgress,'+field+')')
    out+=assertion('sizeof(((PokewalkerIrTransfer*)0)->address) == sizeof(void*)')
    out+=assertion('sizeof(PokewalkerIrPacket) == 8')
    return out


OVERLAY_NATIVE_SOURCES = tuple(dict.fromkeys(OVERLAY_NATIVE_SOURCES + (
    'src/application/pokewalker/pokewalker_ir_requests.c',
    'src/application/pokewalker/pokewalker_ir_status.c',
)))


OVERLAY_NATIVE_SOURCES = tuple(dict.fromkeys(OVERLAY_NATIVE_SOURCES + ("lib/libVCT/src/vct_audio.c", "lib/libVCT/src/vct_fir.c", "lib/libVCT/src/vct_vad.c",)))


def adapt_vct_fir_hw(text):
    text = replace_regex_native(
        text,
        r"reg_CP_DIVCNT = 1;\s*"
        r"\*\(s64 \*\)REG_DIV_NUMER_ADDR = energy;\s*"
        r"\*\(s64 \*\)REG_DIV_DENOM_ADDR = bytes;\s*"
        r"while \(reg_CP_DIVCNT & 0x8000\)\s*\{\s*\}\s*"
        r"return reg_CP_DIV_RESULT_L;",
        "return hg_vct_div64_32(energy, bytes);"
    )
    text = replace_regex_native(
        text,
        r"reg_CP_DIVCNT = 1;\s*"
        r"\*\(s64 \*\)REG_DIV_NUMER_ADDR = energy;\s*"
        r"\*\(s64 \*\)REG_DIV_DENOM_ADDR = length;\s*"
        r"while \(reg_CP_DIVCNT & 0x8000\)\s*\{\s*\}\s*"
        r"\{\s*u32 avg = reg_CP_DIV_RESULT_L;\s*"
        r"reg_CP_SQRTCNT = 0;\s*"
        r"reg_CP_SQRT_PARAM_L = avg;\s*\}\s*"
        r"while \(reg_CP_SQRTCNT & 0x8000\)\s*\{\s*\}\s*"
        r"root = reg_CP_SQRT_RESULT;",
        "root = hg_vct_isqrt32(hg_vct_div64_32(energy, length));"
    )
    return text

def adapt_vct_vad_hw(text):
    pattern = (
        r"reg_CP_SQRTCNT = 0;\s*"
        r"reg_CP_SQRT_PARAM_L = ([^;]+);\s*"
        r"while \(reg_CP_SQRTCNT & 0x8000\)\s*\{\s*\}\s*"
        r"(return|r =)\s*reg_CP_SQRT_RESULT;"
    )
    def substitute(m):
        expr, op = m.group(1), m.group(2)
        return ("return " if op == "return" else "r = ") + (
            f"hg_vct_isqrt32({expr});"
        )
    return replace_regex_native(text, pattern, substitute, 2)

def replace_regex_native(text, pattern, replacement, expected=1):
    result, count = re.subn(pattern, replacement, text, flags=re.M)
    if count != expected:
        raise ValueError(
            f"VCT hardware contract changed: {pattern[:75]}: {count}"
        )
    return result

def _adapt(relative, text, root):
    if relative in POKEWALKER_ABI_INPUTS:
        return pokewalker_abi(relative,text,root)
    if relative == "src/application/ball_capsule_editor.c":
        text = replace(
            text,
            "(int)gBallCapsuleEditorMenuItems[items[i]].func",
            "(items[i] + 1)"
        )
        text = replace(
            text,
            "if (((BOOL(*)(BallCapsuleEditor *))input)(editor) != TRUE) {",
            "if (input < 1 || input > BALL_CAPSULE_MENU_ITEM_SWITCH + 1) {\n"
            "                    GF_ASSERT(FALSE);\n"
            "                    break;\n"
            "                }\n"
            "                if (gBallCapsuleEditorMenuItems[input - 1].func(editor) != TRUE) {"
        )
        return text
    if relative == 'src/global_terminal/global_terminal_socket.c':
        if hashlib.sha256(text.encode()).hexdigest() != 'ccb95e6265138c5f0a21a6c024117b3fbbc946233ad8b23253e40ab01be36f5f':
            raise ValueError('Global Terminal socket ABI source drift')
        anchor = '} GlobalTerminalSocketSettings;'
        checks = r"""
#include <stddef.h>
_Static_assert(sizeof(GlobalTerminalSocket) == 0x280 && _Alignof(GlobalTerminalSocket) == 8, "native socket backing extent");
_Static_assert(offsetof(GlobalTerminalSocket, host) == 0x140, "hostname alias");
_Static_assert(offsetof(GlobalTerminalSocket, unk_200) == 0x200, "settings alias");
_Static_assert(offsetof(GlobalTerminalSocket, port) == 0x240 && offsetof(GlobalTerminalSocketSettings, port) == 0x40, "shared port alias");
_Static_assert(sizeof(GlobalTerminalSocketSettings) == 0x42, "settings is a view, not its assembly reservation");
_Static_assert(sizeof(OSThread) == 0x1a8 && _Alignof(OSThread) == 8, "socket thread native ABI");
_Static_assert(sizeof(OSMutex) == 0x38 && _Alignof(OSMutex) == 8, "socket mutex native ABI");
"""
        text = replace(text, anchor, anchor + checks)
        # The original four-byte opaque host-entry field represents addrType +
        # length, not a native pointer. Use the genuine SDK's canonical ABI.
        for name, native in [('GlobalTerminalSocketAddress', 'SocAddress'),
                             ('GlobalTerminalSocketInAddr', 'SocInAddr'),
                             ('GlobalTerminalSocketHostEntry', 'SocHostEnt')]:
            block = span(text, 'typedef struct ' + name + ' {', '} ' + name + ';')
            text = replace(text, block, 'typedef ' + native + ' ' + name + ';')
        text = replace(text, 'typedef SocHostEnt GlobalTerminalSocketHostEntry;',
            'typedef SocHostEnt GlobalTerminalSocketHostEntry;\n'
            '_Static_assert(sizeof(SocHostEnt) == 32 && offsetof(SocHostEnt, addrList) == 24, "native SDK host-entry ABI");\n'
            '_Static_assert(sizeof(SocAddress) == 8 && offsetof(SocAddress, ip) == 4, "fixed IPv4 address ABI");\n'
            '_Static_assert(sizeof(SocInAddr) == 4, "fixed IPv4 scalar ABI");')
        prototypes = span(text, 'GlobalTerminalSocketHostEntry *SOC_GetHostByName(char *name);',
                          'int SOC_Close(int socket);')
        text = drop(text, prototypes)
        text = replace(text, '**entry->addresses', '*(const u32 *)entry->addrList[0]')
        text = replace(text, 'address.address = sGlobalTerminalSocket.address;',
                       'address.ip = sGlobalTerminalSocket.address;')
        text = replace(text, 'SOC_Connect(sGlobalTerminalSocket.socket, &address)',
                       'SOC_Connect(sGlobalTerminalSocket.socket, &address, sizeof(address))')
        return '#include <nitrowifi/socl_internal.h>\n' + text

    if relative in coordinated.SOURCES:
        text = coordinated.adapt(relative, text)
        if relative in LIBC_DECLARATIONS:
            text = native_libc(relative, text)
        return text
    if relative in SINIT_CALLBACKS:
        callback = SINIT_CALLBACKS[relative]
        original = ('#pragma define_section SINIT ".sinit" abs32 RWX\n'
                    '#pragma section SINIT begin\n'
                    'SDK_FORCE_EXPORT static void (*NitroStaticInit_[])(void) = { ' + callback + ' };\n'
                    '#pragma section SINIT end')
        native = ('SDK_FORCE_EXPORT static void (*NitroStaticInit_[])(void) '
                  '__attribute__((section("__DATA,__ntr_sinit"))) = { ' + callback + ' };')
        return replace(text, original, native)
    if relative == "src/application/pokedex/pokedex_main_seq.c":
        if (text.count("static int PokedexApp_MainSeq_62(PokedexAppData *pokedexApp);") != 1
                or text.count("[POKEDEXAPP_MAINSEQ_62] = PokedexApp_MainSeq_62,") != 1):
            raise ValueError("Pokedex sequence callback contract changed")
        return replace(text, "\nPokedexApp_MainSeq_62(PokedexAppData *pokedexApp) {",
                       "\nstatic int PokedexApp_MainSeq_62(PokedexAppData *pokedexApp) {")
    if relative == "src/field/weather_manager.c":
        original = span(text, "static const sSnowFallSpeeds[]", "\nstatic void Snow_UpdateFlake(WeatherObject *object) {")
        # The final delimiter belongs to the following function, not the block.
        block = original.removesuffix("\nstatic void Snow_UpdateFlake(WeatherObject *object) {")
        if hashlib.sha256(block.encode()).hexdigest() != "2b3e262ffdeac5f0ae1683fb054ee05715acb824ab0a3f155f63509a86c6c604":
            raise ValueError("Snow table declarations or uses changed")
        for table in ("sSnowFallSpeeds", "sSnowSlowdownIntervals"):
            text = replace(text, "static const " + table + "[]", "static const int " + table + "[]")
        for local, table in (("table0", "sSnowSlowdownIntervals"), ("table1", "sSnowFallSpeeds")):
            text = replace(text, local + " = " + table + ";",
                           "memcpy(" + local + ", " + table + ", sizeof(" + local + "));")
        return "#include <string.h>\n" + text
    if relative in PRIVATE_FUNCTIONS or any(relative == entry[0] for entry in PRIVATE_FUNCTIONS.values()):
        return private_declarations(relative, text)
    if relative == "lib/NitroDWC/src/http_engine_request.c":
        # The sole in-tree caller passes 8. Do not silently extend the native
        # signed-length boundary to arbitrary u32 values if the source changes.
        call = "found = NdEngine_StrNCmp(body + start, sStr_returncd_4, 8) == 0;"
        wrapper = "int NdEngine_StrNCmp(const char *a, const char *b, u32 n) {\n    return STD_CompareNString(a, b, n);\n}"
        prototype = "int NdEngine_StrNCmp(const char *a, const char *b, u32 n);"
        if (text.count("NdEngine_StrNCmp(") != 3 or text.count(call) != 1
                or text.count(wrapper) != 1 or text.count(prototype) != 1):
            raise ValueError("HTTP comparison length contract changed")
        return replace(text, "extern int STD_CompareNString(const char *a, const char *b, u32 n);",
                       "#include <nitro/std/string.h>")
    if relative == "lib/libVCT/src/vct_fir.c":
        return '\n#include <stdint.h>\n\nstatic uint32_t hg_vct_isqrt32(uint32_t n) {\n    uint32_t r = 0, bit = UINT32_C(1) << 30;\n    while (bit > n) bit >>= 2;\n    while (bit) {\n        if (n >= r + bit) {\n            n -= r + bit;\n            r = (r >> 1) + bit;\n        } else {\n            r >>= 1;\n        }\n        bit >>= 2;\n    }\n    return r;\n}\n\n\nstatic uint32_t hg_vct_div64_32(int64_t numerator, int32_t denominator) {\n    return (uint32_t)(numerator / denominator);\n}\n\n' + adapt_vct_fir_hw(text)
    if relative == "lib/libVCT/src/vct_vad.c":
        return '\n#include <stdint.h>\n\nstatic uint32_t hg_vct_isqrt32(uint32_t n) {\n    uint32_t r = 0, bit = UINT32_C(1) << 30;\n    while (bit > n) bit >>= 2;\n    while (bit) {\n        if (n >= r + bit) {\n            n -= r + bit;\n            r = (r >> 1) + bit;\n        } else {\n            r >>= 1;\n        }\n        bit >>= 2;\n    }\n    return r;\n}\n\n' + adapt_vct_vad_hw(text)
    if relative == "lib/libVCT/src/vct_audio.c":
        text = replace(text, '    reg_CP_SQRTCNT = 0;\n    reg_CP_SQRT_PARAM_L = power;\n    while (reg_CP_SQRTCNT & 0x8000) {}\n    root = reg_CP_SQRT_RESULT;', '    root = hg_vct_isqrt32(power);')
        text = '#include <stdint.h>\nstatic uint32_t hg_vct_isqrt32(uint32_t n) {\n    uint32_t r = 0, bit = UINT32_C(1) << 30;\n    while (bit > n) bit >>= 2;\n    while (bit) {\n        if (n >= r + bit) {\n            n -= r + bit;\n            r = (r >> 1) + bit;\n        } else r >>= 1;\n        bit >>= 2;\n    }\n    return r;\n}\n' + text

        return text + '\nu32 hg_vct_audio_flag(void) { return sAudioFlag; }\nu32 hg_vct_audio_sessions(void) { return sAudioSessions; }\nu32 hg_vct_audio_packet_size(void) { return sAudioPacketSize; }\n'
    if relative == "lib/libVCT/src/vct_audio_send.c":
        text = replace(
            text,
            "asm { clz x, x }",
            "x = x == 0 ? 32u : (u32)__builtin_clz(x);"
        )
        begin = "// View of the audio TU's pooled .bss"
        end_marker = "extern AudioPool _021D6040;"
        if text.count(begin) != 1 or text.count(end_marker) != 1:
            raise ValueError("Original AudioPool declaration drift")
        a = text.index(begin)
        b = text.index(end_marker) + len(end_marker)
        declarations = (
            '#include "vct/vct_audio_internal.h"\n'
            "extern u32 hg_vct_audio_flag(void);\n"
            "extern u32 hg_vct_audio_sessions(void);\n"
            "extern u32 hg_vct_audio_packet_size(void);\n"
        )
        text = text[:a] + declarations + text[b:]
        if text.count('_021D6040.unk_18') != 1:
            raise ValueError("VCT access drift: _021D6040.unk_18")
        text = text.replace('_021D6040.unk_18', 'hg_vct_audio_flag()')
        if text.count('_021D6040.unk_20') != 1:
            raise ValueError("VCT access drift: _021D6040.unk_20")
        text = text.replace('_021D6040.unk_20', 'hg_vct_audio_sessions()')
        if text.count('_021D6040.packetSize') != 1:
            raise ValueError("VCT access drift: _021D6040.packetSize")
        text = text.replace('_021D6040.packetSize', 'hg_vct_audio_packet_size()')
        if text.count('_021D6040.sendRead') != 1:
            raise ValueError("VCT access drift: _021D6040.sendRead")
        text = text.replace('_021D6040.sendRead', 'sSendInfo.read')
        if text.count('_021D6040.sendPacket') != 4:
            raise ValueError("VCT access drift: _021D6040.sendPacket")
        text = text.replace('_021D6040.sendPacket', 'sSendInfo.packet')
        if text.count('_021D6040.sendMask') != 4:
            raise ValueError("VCT access drift: _021D6040.sendMask")
        text = text.replace('_021D6040.sendMask', 'sSendInfo.mask')
        if text.count('_021D6040.sendSlot') != 2:
            raise ValueError("VCT access drift: _021D6040.sendSlot")
        text = text.replace('_021D6040.sendSlot', 'sSendInfo.balanceIndex')
        if text.count('_021D6040.sendBalance') != 1:
            raise ValueError("VCT access drift: _021D6040.sendBalance")
        text = text.replace('_021D6040.sendBalance', 'sSendInfo.balance')
        if "_021D6040." in text:
            raise ValueError("Unmapped AudioPool field")
        return text
    if relative == "lib/libVCT/src/vct_packet_buffer.c":
        # ARM64 physical slot geometry; retain the original algorithm.
        for old, new in (
            ('count * sizeof(PacketBuffer)', 'count * HG_VCT_NATIVE_SLOT_SIZE'),
            ('current->next = base + index;', 'current->next = (PacketBuffer *)((u8 *)base + index * HG_VCT_NATIVE_SLOT_SIZE);'),
            ('offset += sizeof(PacketBuffer);', 'offset += HG_VCT_NATIVE_SLOT_SIZE;'),
            ('gVctPacketBuffers[1][count - 1].next = NULL;', '((PacketBuffer *)((u8 *)gVctPacketBuffers[1] + (count - 1) * HG_VCT_NATIVE_SLOT_SIZE))->next = NULL;'),
            ('u32 count = bytes / sizeof(PacketBuffer);', 'u32 count = bytes / HG_VCT_NATIVE_SLOT_SIZE;'),
            ('if ((u32)buffer & 31)', 'if ((uintptr_t)buffer & 31)'),
        ):
            text = replace(text, old, new)
        return '#include <stdint.h>\n#include <vct/vct_ssp_internal.h>\n#include <vct/vct_audio_internal.h>\n#define HG_VCT_NATIVE_SLOT_SIZE ((sizeof(AudioPacket) > sizeof(PacketBuffer)) ? sizeof(AudioPacket) : sizeof(PacketBuffer))\n' + text

    if relative == "include/voice_chat.h":
        # Native storage capacity, not a gameplay/session-count change.
        return replace(text, "VctSession sessions[3];",
                       "VctSession sessions[8];")
    if relative == "src/voice_chat.c":
        for declaration in (
            "extern void MIC_StartAutoSamplingAsync(MICAutoParam *param, void (*callback)(MICResult, void *), void *arg);",
            "extern u8 *MIC_GetLastSamplingAddress(void);",
            "extern void MIC_StopAutoSampling(void);",
        ):
            text = drop(text, declaration)
        # C's void* conversion supplies the original byte view, with no change
        # to the offset test or the callback/sampling behavior.
        text = replace(text,
            "    if ((u32)(MIC_GetLastSamplingAddress() - address) < size) {",
            "    u8 *lastSamplingAddress = MIC_GetLastSamplingAddress();\n"
            "    if ((u32)(lastSamplingAddress - address) < size) {")

        # Preserve eight packet slots per participant with native stride.
        if text.count("count * 0x23C0 + 32") != 2:
            raise ValueError("Voice-chat packet capacity source drift")
        text = text.replace(
            "count * 0x23C0 + 32",
            "count * (8 * HG_VCT_NATIVE_SLOT_SIZE) + 32")
        # Native ARM64 storage-width adaptation. Preserve the original
        # allocation algorithm; only remove the DS 32-bit pointer assumptions.
        text = replace(text,
            "    u32 allocation;",
            "    void *allocation;")
        text = replace(text,
            "VoiceChat_AllocAligned((void **)&allocation,",
            "VoiceChat_AllocAligned(&allocation,")
        text = replace(text,
            "    *aligned = (void *)(((u32)*allocation + 0x1F) & ~0x1F);",
            "    *aligned = (void *)(((uintptr_t)*allocation + 0x1F) & ~(uintptr_t)0x1F);")
        return '#include <nitro/spi/ARM9/mic.h>\n#include <stdint.h>\n#include <vct/vct_ssp_internal.h>\n#include <vct/vct_audio_internal.h>\n#define HG_VCT_NATIVE_SLOT_SIZE ((sizeof(AudioPacket) > sizeof(PacketBuffer)) ? sizeof(AudioPacket) : sizeof(PacketBuffer))\n' + text
    if relative in PRINTF_DECLARATIONS:
        if relative in LIBC_DECLARATIONS:
            text = native_libc(relative, text)
        for declaration in PRINTF_DECLARATIONS[relative]:
            text = drop(text, declaration)
        return '#include <nitro/os/common/printf.h>\n' + text
    if relative in QSORT_DECLARATIONS:
        text = replace(text, QSORT_DECLARATIONS[relative], "#include <nitro/math/qsort.h>")
        if relative == "src/application/pokewalker/pokewalker_event_log.c":
            text = replace(text,
                "static int PokewalkerEventLog_CompareEntryTimes(PokewalkerEventLogSlot *a, PokewalkerEventLogSlot *b) {",
                "static int PokewalkerEventLog_CompareEntryTimes(const void *first, const void *second) {\n"
                "    const PokewalkerEventLogSlot *a = first;\n    const PokewalkerEventLogSlot *b = second;")
            text = replace(text, "(int (*)(const void *, const void *, void *))PokewalkerEventLog_CompareEntryTimes", "PokewalkerEventLog_CompareEntryTimes")
        return text
    if relative in LIBC_DECLARATIONS:
        return native_libc(relative, text)
    return adapt_original(relative, text, root)


def adapt(relative, text, root):
    record = coordinated.HEADER_ROUTES.get(relative)
    if record and hashlib.sha256(text.encode()).hexdigest() != record['sha256']:
        raise ValueError('Native header routing source drift: ' + relative)
    bounded = COMPILER_BOUNDED_OPERATIONS.get(relative)
    if bounded and hashlib.sha256(text.encode()).hexdigest() != bounded[0]:
        raise ValueError("Bounded compiler source drift: " + relative)
    arm = ARM_INLINE_OPERATIONS.get(relative)
    if arm and hashlib.sha256(text.encode()).hexdigest() != arm[0]:
        raise ValueError("ARM inline source drift: " + relative)
    operation = COMPILER_OPERATIONS.get(relative)
    if operation and hashlib.sha256(text.encode()).hexdigest() != operation[0]:
        raise ValueError("Compiler arithmetic source drift: " + relative)
    try:
        result = _adapt(relative, text, root)
    except ValueError as error:
        if not (record or operation or arm or bounded) or str(error) != 'No native adaptation is registered for ' + relative:
            raise
        result = text
    if bounded:
        for old, new, count in bounded[1]:
            result = replace(result, old, new, count=count)
    if arm:
        for old, new in arm[1]:
            result = replace(result, old, new)
    if operation:
        _, declaration, old, new = operation
        result = replace(drop(result, declaration), old, new)
    if record:
        for old, new in record['edits']:
            if old in result:
                result = result.replace(old, new)
            elif new not in result:
                raise ValueError('Native header routing fragment changed: ' + relative + ': ' + old)
    if relative == 'src/application/pokewalker/pokewalker_ir.c':
        result=replace(result,'void *data, u32 address, int size','void *data, uintptr_t address, int size')
        result=replace(result,'(u32)buffer & 3','(uintptr_t)buffer & 3')
        # The final u16 is the original wire address; only the intermediate
        # host pointer conversion changes width.
        result=replace(result,'(u16)(u32)gPokewalkerIrTransfer.data','(u16)(uintptr_t)gPokewalkerIrTransfer.data')
        result,count=re.subn(r'\(u32\)(?=\(?gPokewalkerIrWork\.(?:status|blocks|records|walkerMon)\b)','(uintptr_t)',result)
        if count!=9: raise ValueError('Pokewalker destination casts changed: '+str(count))
        result=replace(result,'&gPokewalkerIrSync','&gPokewalkerIrSync.mutex',count=5)
        result=replace(result,'gPokewalkerIrBuffers, 1','gPokewalkerIrWork.messages, 1')
        result=result.replace('gPokewalkerIrTransfer.', 'gPokewalkerIrSync.')
        result=result.replace('&gPokewalkerIrMessageQueue','&gPokewalkerIrSync.queue')
        result=result.replace('sizes = gPokewalkerIrImageSizes;', 'sizes = &gPokewalkerIrWork.compressedImageSizes;')
        result=result.replace('sizes = gPokewalkerIrStrollSizes;', 'sizes = &gPokewalkerIrWork.compressedStrollSizes;')
        result += '''
_Static_assert(sizeof(PokewalkerIrLink) == 80 && _Alignof(PokewalkerIrLink) == 8, "native link storage");
_Static_assert(sizeof(OSThread) == 424 && _Alignof(OSThread) == 8, "native thread storage");
_Static_assert(sizeof(PokewalkerIrPacket) == 8 && sizeof(PokewalkerIrClock) == 40, "serialized IR packet and clock");
_Static_assert(sizeof(PokewalkerIrIdentity) == 104 && sizeof(PokewalkerMon) == 16, "serialized IR identity and mon");
_Static_assert(sizeof(PokewalkerIrRecord) == 136 && sizeof(PokewalkerIrStatus) == 3404, "serialized IR records");
_Static_assert(sizeof(PokewalkerIrBlocks) == 1736, "serialized IR blocks");
'''
    return result


def adapt_original(relative, text, root):
    if relative == "lib/include/nnsys/g2d/g2d_CellTransferManager.h":
        return replace(text, "\nNNS_G2dInitCellTransferStateManager(", "\nint NNS_G2dInitCellTransferStateManager(")
    if relative == "lib/NitroSystem/src/fnd_expheap.c":
        # Host-address adaptation of the unchanged original allocator.
        # Fail if any expected original expression changes.
        changes = [
            ("return (u8 *)(size + (u32)start);",
             "return start + size;"),
            ("region->end = (u8 *)(block->blockSize + (u32)(block + 1));",
             "region->end = (u8 *)(block + 1) + block->blockSize;"),
            ("freeRgnB.start = (u8 *)(size + (u32)address);",
             "freeRgnB.start = address + size;"),
            ("(u8 *)((alignment + (u32)start) & ~alignment)",
             "(u8 *)(((uintptr_t)start + (uintptr_t)alignment) & ~(uintptr_t)alignment)"),
            ("(u8 *)(block->blockSize + (u32)start)",
             "(start + block->blockSize)"),
            ("(u8 *)((u32)(end - size) & ~(alignment - 1))",
             "(u8 *)((uintptr_t)(end - size) & ~(uintptr_t)(alignment - 1))"),
            ("(u32)block < (u32)region->start",
             "(uintptr_t)block < (uintptr_t)region->start"),
            ("(u8 *)(oldSize + ((u32)block + sizeof(ExpHeapBlock)))",
             "((u8 *)(block + 1) + oldSize)"),
            ("(u8 *)(size + (u32)data)",
             "(data + size)"),
            ("(u8 *)(block->blockSize + ((u32)block + sizeof(ExpHeapBlock)))",
             "((u8 *)(block + 1) + block->blockSize)"),
        ]
        for before, after in changes:
            expected = 2 if before == "(u8 *)(size + (u32)data)" else 1
            if text.count(before) != expected:
                raise ValueError("Original ExpHeap expression changed: " + before)
            text = text.replace(before, after, expected)

        # Native metadata contains pointers and requires 8-byte alignment.
        # Preserve requested alignment when it is stricter.
        before_alloc = """    if (size == 0) {
        size = 1;
    }
    size = (size + 3) & ~3;
    if (alignment >= 0) {
        return AllocFromHead__ExpHeap((ExpHeap *)heap, size, alignment);
    }
    return AllocFromTail__ExpHeap((ExpHeap *)heap, size, -alignment);"""
        after_alloc = """    const u32 mask = _Alignof(ExpHeapBlock) - 1;
    if (size == 0) {
        size = 1;
    }
    if (size > UINT32_MAX - mask) {
        return NULL;
    }
    size = (size + mask) & ~mask;
    if (alignment >= 0) {
        if (alignment < (int)_Alignof(ExpHeapBlock)) {
            alignment = _Alignof(ExpHeapBlock);
        }
        return AllocFromHead__ExpHeap((ExpHeap *)heap, size, alignment);
    }
    if (alignment > -(int)_Alignof(ExpHeapBlock)) {
        alignment = -(int)_Alignof(ExpHeapBlock);
    }
    return AllocFromTail__ExpHeap((ExpHeap *)heap, size, -alignment);"""
        if text.count(before_alloc) != 1:
            raise ValueError("Original ExpHeap allocation entry changed")
        text = text.replace(before_alloc, after_alloc, 1)

        before_resize = """    oldSize = block->blockSize;
    size = (size + 3) & ~3;
    if (size == oldSize) {"""
        after_resize = """    oldSize = block->blockSize;
    const u32 mask = _Alignof(ExpHeapBlock) - 1;
    if (size > UINT32_MAX - mask) {
        return 0;
    }
    size = (size + mask) & ~mask;
    if (size == oldSize) {"""
        if text.count(before_resize) != 1:
            raise ValueError("Original ExpHeap resize entry changed")
        text = text.replace(before_resize, after_resize, 1)

        before = """    u8 *end = (u8 *)((size + (u32)startAddress) & ~3);
    startAddress = (void *)(((u32)startAddress + 3) & ~3);
    if ((u32)startAddress > (u32)end || (u32)(end - (u8 *)startAddress) < sizeof(ExpHeap) + sizeof(ExpHeapBlock) + 4) {
        return NULL;
    }
    return (NNSFndHeapHandle)InitExpHeap(startAddress, end, optFlag);"""
        after = """    uintptr_t begin = (uintptr_t)startAddress;
    uintptr_t alignment = _Alignof(ExpHeap);
    if (_Alignof(ExpHeapBlock) > alignment) {
        alignment = _Alignof(ExpHeapBlock);
    }
    uintptr_t mask = alignment - 1;
    if (begin > UINTPTR_MAX - size || begin > UINTPTR_MAX - mask) {
        return NULL;
    }
    uintptr_t end = (begin + size) & ~mask;
    uintptr_t aligned = (begin + mask) & ~mask;
    if (aligned > end ||
        end - aligned < sizeof(ExpHeap) + sizeof(ExpHeapBlock) + 4) {
        return NULL;
    }
    return (NNSFndHeapHandle)InitExpHeap((void *)aligned, (void *)end, optFlag);"""
        if text.count(before) != 1:
            raise ValueError("Original ExpHeap constructor changed")
        text = text.replace(before, after, 1)

        return "#include <stdint.h>\\n" + text
    if relative == "lib/NitroSystem/src/fnd_heapcommon.c":
        # Original assembly provides these BSS globals, but its 32-bit
        # storage sizes cannot represent the native pointer-bearing list.
        text = replace(
            text,
            "extern BOOL gFndRootHeapListInitialized;",
            "BOOL gFndRootHeapListInitialized;",
        )
        text = replace(
            text,
            "extern NNSFndList gFndRootHeapList;",
            "NNSFndList gFndRootHeapList;",
        )

        # Preserve the original list algorithm. Only the layout-dependent
        # offset changes: 4 on ARM32, 8 on native ARM64.
        offset = "offsetof(NNSiFndHeapHead, link)"
        text = replace(
            text,
            "NNS_FndInitList(&heap->childList, 4);",
            f"NNS_FndInitList(&heap->childList, {offset});",
        )
        text = replace(
            text,
            "NNS_FndInitList(&gFndRootHeapList, 4);",
            f"NNS_FndInitList(&gFndRootHeapList, {offset});",
        )

        return "#include <stddef.h>\n" + text
    if relative == "include/wifi_setup/wifi_setup_ui.h":
        declaration = span(text, "typedef struct WifiSetupArchiveState {", "} WifiSetupArchiveState;")
        if hashlib.sha256(declaration.encode()).hexdigest() != 'a99d3caacb38b136f9e1c8d51500b6e04fb362c10ee2087335cc0f61e90a1f58':
            raise ValueError("Original Wi-Fi archive layout changed")
        original = "    u8 unk_88[0xE4 - 0x88 - sizeof(FSArchive)];"
        text = replace(text, original, "#ifndef SDK_64BIT\n" + original + "\n#endif")
        checks = ("\n#ifdef SDK_64BIT\n"
            '_Static_assert(_Alignof(WifiSetupArchiveState) >= _Alignof(FSArchive), "Archive state alignment");\n'
            '_Static_assert(offsetof(WifiSetupArchiveState, arc) % _Alignof(FSArchive) == 0, "Embedded archive alignment");\n'
            '_Static_assert(offsetof(WifiSetupArchiveState, lockId) == offsetof(WifiSetupArchiveState, arc) + sizeof(FSArchive), "Native archive has no DS tail padding");\n'
            '_Static_assert(sizeof(WifiSetupArchiveState) <= 0xffffffffu, "Archive allocation size fits u32");\n'
            "#endif\n")
        return replace(text, "} WifiSetupArchiveState;", "} WifiSetupArchiveState;" + checks)
    if relative == "src/wifi_setup/wifi_setup_share.c":
        original = "WifiSetupHeap_AllocZeroed(sizeof(WifiSetupArchiveState), 4)"
        return replace(text, original,
            "WifiSetupHeap_AllocZeroed(sizeof(WifiSetupArchiveState), _Alignof(WifiSetupArchiveState))")
    if relative == "src/party_menu_list_items.c":
        entries, table = party_actions(text)
        original = span(text, "static const u32 _02101CB8[] = {", "\n};")
        text = replace(text, original, table)
        dispatch = "".join(f"        [{name}] = {callback},\n" for name, callback in entries)
        return text + ("\nvoid HG_PartyMenu_InvokeAction(u32 action, PartyMenu *menu, int *state) {\n"
                       "    static const PartyMonContextMenuActionFunc actions[PARTY_MON_CONTEXT_MENU_MAX] = {\n"
                       + dispatch + "    };\n"
                       "    if (action >= PARTY_MON_CONTEXT_MENU_MAX || !actions[action]) __builtin_trap();\n"
                       "    actions[action](menu, state);\n}\n")
    if relative == "src/party_menu.c":
        for arg in ("&result", "(int *)pState"):
            text = replace(text, f"((PartyMonContextMenuActionFunc)func)(partyMenu, {arg});",
                           f"HG_PartyMenu_InvokeAction(func, partyMenu, {arg});")
        return ("struct PartyMenu;\nextern void HG_PartyMenu_InvokeAction(unsigned int, struct PartyMenu *, int *);\n"
                f'#line 1 {json.dumps(str(root / relative), ensure_ascii=False)}\n' + text)
    if relative == "src/comm_state_private.h":
        text = drop(text, "typedef struct {\n    u64 x;\n    u64 mul;\n    u64 add;\n} MATHRandContext32;")
        original = (root / "src/comm_state.c").read_text()
        private = set(re.findall(r"^static\s+(?:void|BOOL|s32|int)\s+(CommState_\w+)\(", original, re.M))
        if len(private) != 77:
            raise ValueError("CommState private helper definitions changed")
        # These definitions are file-local; do not export them to satisfy bad declarations.
        for name in sorted(private):
            text, count = re.subn(r"^(?:void|BOOL|s32|int) " + name + r"\([^;\n]*;", "", text, flags=re.M)
            if count != 1:
                raise ValueError("Private CommState declaration changed: " + name)
        text = replace(text, "int DWC_Init(int);", "int DWC_Init(void *work);")
        return replace(text, '#include "global.h"', '#include "global.h"\n#include <nitro/math/rand.h>')
    if relative == "src/comm_state.c":
        text = replace(text, "    void (*const linkedStates[3])(void);\n    ARRAY_ASSIGN(linkedStates, gCommLinkedStates);",
                       "    void (*const *linkedStates)(void) = gCommLinkedStates;")
        text = replace(text, "DWC_Init(((u32)work + 31) & ~31)",
                       "DWC_Init((void *)(((uintptr_t)work + 31) & ~(uintptr_t)31))")
        return "#include <stdint.h>\n" + text
    if relative == "src/wireless_manager.c":
        checks = span(text, "typedef char WirelessWorkSizeCheck", "typedef char WirelessWorkBeaconCheck[offsetof(WirelessWork, beaconCount) == 0x1345 ? 1 : -1];")
        text = replace(text, checks, "#ifndef SDK_64BIT\n" + checks + "\n#endif")
        old = "    u32 p = (u32)buffer;\n    u32 mod;\n\n    mod = p << 27;\n    mod = mod >> 27;\n    if (mod != 0) {\n        p += 32 - mod;\n    }"
        text = replace(text, old, "    uintptr_t p = ((uintptr_t)buffer + 31) & ~(uintptr_t)31;")
        text = drop(text, "void WVR_TerminateAsync(void (*callback)(void *), void *arg);")
        return "#include <stdint.h>\n" + text
    if relative == "src/comm_wireless.c":
        check = "typedef char CommWirelessWorkSizeCheck[sizeof(CommWirelessWork) == 0xD98 ? 1 : -1];"
        text = replace(text, check, "#ifndef SDK_64BIT\n" + check + "\n#endif")
        text = drop(text, "int WVR_StartUpAsync(int mode, void (*callback)(void *, int), void *arg);\nint WVR_TerminateAsync(void (*callback)(void *), void *arg);")
        wrappers = ("\nstatic void HG_WVR_StartCallback(void *arg, WVRResult result) {\n"
                    "    CommWireless_OnStartedUp(arg, result != WVR_RESULT_SUCCESS);\n}\n"
                    "static void HG_WVR_TerminateCallback(void *arg, WVRResult result) {\n"
                    "    if (result != WVR_RESULT_SUCCESS) { OS_Terminate(); return; }\n"
                    "    CommWireless_OnTerminated(arg);\n}\n")
        text = replace(text, "static void CommWireless_OnTerminated(void *unused);",
                       "static void CommWireless_OnTerminated(void *unused);" + wrappers)
        text = replace(text, "WVR_StartUpAsync(8, CommWireless_OnStartedUp, NULL) != 1",
                       "WVR_StartUpAsync(8, HG_WVR_StartCallback, NULL) != WVR_RESULT_OPERATING")
        text = replace(text, "WVR_TerminateAsync(CommWireless_OnTerminated, NULL)",
                       "WVR_TerminateAsync(HG_WVR_TerminateCallback, NULL)")
        text = replace(text, "misalignment = (u32)buffer & 0x1F;", "misalignment = (u32)((uintptr_t)buffer & 0x1F);")
        return "#include <stdint.h>\n" + text
    if relative == "src/code_entry.c":
        for reg in ("REG_BLDCNT_ADDR", "REG_DB_BLDCNT_ADDR"):
            text = replace(text, f"G2x_SetBlendAlpha_({reg},", f"G2x_SetBlendAlpha_((u64){reg},")
        return text
    if relative == "src/spin_trade_link.c":
        return drop(text, "u32 MATH_CountPopulation(u32 value);")
    if relative in ("include/drawing_session_link_internal.h", "include/record_mixing/record_mixing_link_internal.h", "lib/include/nitro/wm/wm_internal.h", "lib/include/vct/vct_audio_internal.h"):
        declaration = {"include/drawing_session_link_internal.h": "int MATH_CountPopulation(u32);",
                       "include/record_mixing/record_mixing_link_internal.h": "u32 MATH_CountPopulation(u32);",
                       "lib/include/nitro/wm/wm_internal.h": "int MATH_CountPopulation(u32 value);",
                       "lib/include/vct/vct_audio_internal.h": "int MATH_CountPopulation(u32 value);"}[relative]
        return drop(text, declaration)
    if relative == "include/field/field_fog.h":
        return drop(text, "void G3X_SetFogTable(u32 *fogTable);")
    if relative == "lib/include/nnsys/g3d_render_internal.h":
        for name in ("G3X_GetClipMtx", "G3X_GetVectorMtx"):
            text = drop(text, f"u32 {name}(void *dst);")
        return replace(text,
            'void NNSi_G3dFuncSbc_SHP_InternalDefault(G3dRS *pRS, u32 opt, const G3dResShpData *pShpData);',
            'void NNSi_G3dFuncSbc_SHP_InternalDefault(G3dRS *pRS, u32 opt, const G3dResShpData *pShpData, u32 unusedShpID);')
    if relative in ("lib/NitroSystem/src/gfd_vram_transfer_manager.c", "lib/NitroSystem/src/g3d_kernel.c"):
        names = ["GX_LoadTex", "GX_LoadTexPltt"]
        if relative.endswith("gfd_vram_transfer_manager.c"):
            names += ["GX_LoadClearImageColor", "GX_LoadClearImageDepth"]
        for name in names:
            text = replace(text, f"void {name}(void *src,", f"void {name}(const void *src,")
        if relative.endswith('g3d_kernel.c'):
            # Original allocation formula rounds the fixed header plus node/
            # material u16 map entries. Only the native header/align change;
            # serialized resources and the count/dispatch algorithm do not.
            text = '#include <stddef.h>\n' + text
            for count in ('numMat','numNode'):
                text = replace(text, f'(pResMdl->info.{count} * 2 + 0x1C) & ~3',
                    f'(offsetof(NNSG3dAnmObj,mapData) + pResMdl->info.{count} * sizeof(u16) + '
                    '(_Alignof(NNSG3dAnmObj)-1)) & ~(_Alignof(NNSG3dAnmObj)-1)')
        return text
    if relative in ("lib/NitroSystem/src/g2d_char_canvas.c", "lib/NitroSystem/src/g2d_char_canvas_util.c", "lib/NitroSystem/src/g2d_canvas_arrange.c"):
        return replace(text, "asm { clz x, x }", "x = x ? __builtin_clz((unsigned int)x) : 32;")
    if relative == "src/save_fashion.c":
        text = drop(text, "void MATHi_CRC32InitTableRev(u32 *table, u32 polynomial);")
        text = drop(text, "u32 MATH_CalcCRC32(const u32 *table, const void *data, u32 size);")
        text = replace(text, "    u32 table[256];", "    MATHCRC32Table storage;\n    MATHCRC32Table *table = &storage;")
        return text
    if relative == "src/screen_fade_effects.c":
        return drop(text, "static inline int GX_IsHBlank(void) {\n    return reg_GX_DISPSTAT & REG_GX_DISPSTAT_HBLK_MASK;\n}")
    if relative == "lib/include/nitro/os/ownerInfo.h":
        if hashlib.sha256(text.encode()).hexdigest() != "6d2be5a4fc3b525bab2fbccbe9491e64aee4ff4206b479e958b1fac51452e67d":
            raise ValueError("Original owner-info declarations changed")
        return ("#ifndef NITRO_OS_OWNERINFO_H_\n#define NITRO_OS_OWNERINFO_H_\n#include <stddef.h>\n"
                "#include <nitro/os/common/ownerInfo.h>\n"
                '_Static_assert(sizeof(OSBirthday) == 2 && sizeof(OSOwnerInfo) == 84, "DS owner data sizes");\n'
                '_Static_assert(offsetof(OSOwnerInfo, birthday) == 2 && offsetof(OSOwnerInfo, nickName) == 4, "DS owner fields");\n'
                '_Static_assert(offsetof(OSOwnerInfo, nickNameLength) == 26 && offsetof(OSOwnerInfo, comment) == 28 && offsetof(OSOwnerInfo, commentLength) == 82, "DS owner text offsets");\n'
                "#endif\n")
    if relative == "include/orbit_cursor.h":
        checks = span(text, "typedef char AssertTouchSpriteSize", "typedef char AssertTouchTask[(offsetof(OrbitCursor, task) == 0xF4) ? 1 : -1];")
        native = ('_Static_assert(offsetof(OrbitCursor, sprites) % _Alignof(OrbitCursorSprite) == 0, "Native sprite alignment");\n'
                  '_Static_assert(offsetof(OrbitCursor, task) % _Alignof(void *) == 0, "Native task pointer alignment");')
        return replace(text, checks, "#ifndef SDK_64BIT\n" + checks + "\n#else\n" + native + "\n#endif")
    if relative == "lib/NitroDWC/src/tree-iterator4.h":
        expected = "typedef struct Iterator {\n    void *current;\n#ifdef __cplusplus\n    void Advance();\n#endif\n} Iterator;"
        if span(text, "typedef struct Iterator {", "} Iterator;") != expected:
            raise ValueError("Original Iterator layout changed")
        original = "typedef char DwcTreeIteratorSize4[sizeof(Iterator)==4?1:-1];"
        checks = ("#ifndef SDK_64BIT\n" + original + "\n#else\n"
                  "typedef char DwcTreeIteratorNativeSize[sizeof(Iterator)==sizeof(void*)?1:-1];\n"
                  "typedef char DwcTreeIteratorNativeOffset[offsetof(Iterator,current)==0?1:-1];\n"
                  "typedef char DwcTreeIteratorNativeMember[sizeof(((Iterator*)0)->current)==sizeof(void*)?1:-1];\n"
                  "#ifdef __cplusplus\n"
                  "static_assert(alignof(Iterator)==alignof(void*), \"Iterator alignment\");\n"
                  "#else\n"
                  "_Static_assert(_Alignof(Iterator)==_Alignof(void*), \"Iterator alignment\");\n"
                  "#endif\n#endif")
        return '#include <stddef.h>\n' + replace(text, original, checks)
    if relative in SOUND_FILES:
        declarations, pointer_casts = SOUND_FILES[relative]
        text = callbacks(text, declarations)
        if relative.endswith("snd_internal.h"):
            pm = span(text, "typedef struct PmSleepCallback {", "} PmSleepCallback;")
            text = replace(text, pm, "typedef PMSleepCallbackInfo PmSleepCallback;")
            for name in ("PM_PrependPreSleepCallback", "PM_AppendPostSleepCallback", "PM_DeletePreSleepCallback", "PM_DeletePostSleepCallback"):
                text = drop(text, f"void {name}(PmSleepCallback *info);")
            driver = '#define SND_DRIVER_INFO_SIZE 0x11E0\n\ntypedef struct SndDriverInfo {\n    u8 data[SND_DRIVER_INFO_SIZE];\n} SndDriverInfo;'
            text = replace(text, driver, '#define SND_DRIVER_INFO_SIZE sizeof(SNDDriverInfo)\ntypedef SNDDriverInfo SndDriverInfo;')
            for declaration in SOUND_DECLARATIONS:
                text = drop(text, declaration)
            # Teach C's optimizer the same ownership as the exported labels.
            # Otherwise distinct extern objects may be assumed disjoint even
            # though Mach-O resolves their addresses to the same storage.
            text = '#include <stddef.h>\n' + text
            for view in ("U16", "U32", "U8"):
                text = replace(text, f"}} SndPlayerInfo{view}View;",
                               f"}} __attribute__((may_alias)) SndPlayerInfo{view}View;")
            for name, (owner, ctype, member) in STORAGE_ALIASES.items():
                if not owner.startswith('gSnd'): continue
                if owner == "gSndPlayerInfo":
                    view = {"playerList.numObjects": "U16", "volume": "U8"}.get(member, "U32")
                    expression = f"((SndPlayerInfo{view}View *)((unsigned char *){owner} + offsetof({ctype}, {member})))"
                else:
                    expression = f"({owner}.{member})"
                text += f"\n#define {name} {expression}\n"

        elif relative.endswith("snd_arc_internal.h"):
            text = drop(text, "void SND_AssignWaveArc(void *bank, int index, void *waveArc);")
            text = replace(text, "} SndHeapBlock;", "} __attribute__((aligned(32))) SndHeapBlock;")
            text += ('\n_Static_assert(sizeof(SndHeapBlock) % 32 == 0 && _Alignof(SndHeapBlock) == 32, "Sound payload alignment");\n'
                     '_Static_assert(sizeof(((SndHeapBlock *)0)->data1) == sizeof(uintptr_t), "Sound callback pointer width");\n')
        elif relative.endswith("snd_arc_strm_internal.h"):
            for first, last, alias in (("typedef struct SndInstPos {", "} SndInstPos;", "typedef SNDInstPos SndInstPos;"),
                                       ("typedef struct SndInstData {", "} SndInstData;", "typedef SNDInstData SndInstData;")):
                text = replace(text, span(text, first, last), alias)
            for declaration in WAVE_DECLARATIONS:
                text = drop(text, declaration)
            text += ('\n_Static_assert(sizeof(SNDInstPos) == 8 && sizeof(SNDInstData) == 12, "DS instrument data widths");\n'
                     '_Static_assert(__builtin_offsetof(SNDInstData, param.wave[0]) == 2 && __builtin_offsetof(SNDInstData, param.wave[1]) == 4, "DS instrument wave fields");\n')
        elif relative.endswith("snd_arc_loader_wave.c"):
            text = replace(text, "instData.waveNo", "instData.param.wave[0]")
            text = replace(text, "instData.waveArcIdx", "instData.param.wave[1]")
            text = replace(text, "start = (u32)SND_GetWaveDataAddress(table, index);", "start = SND_GetWaveDataAddress(table, index) != NULL;")
        elif relative.endswith("snd_heap.c"):
            text = replace(text, "u32 alignedAddr = (u32)buffer + 3;", "uintptr_t alignedAddr = (uintptr_t)buffer + _Alignof(struct NNSSndHeap) - 1;")
            text = replace(text, "u8 *start = (u8 *)(alignedAddr & ~3);", "u8 *start = (u8 *)(alignedAddr & ~((uintptr_t)_Alignof(struct NNSSndHeap) - 1));")
        text, count = re.subn(r"\(u32\)(arc|table)\b", r"(uintptr_t)\1", text)
        if count != pointer_casts:
            raise ValueError("Sound callback pointer casts changed: " + relative)
        return text
    if relative in ("lib/NitroSystem/src/snd_system.c", "lib/NitroSystem/src/snd_stream.c"):
        text = replace(text, "preSleep.func", "preSleep.callback")
        return replace(text, "postSleep.func", "postSleep.callback")
    raise ValueError("No native adaptation is registered for " + relative)


SOUND_DECLARATIONS = (
    "const void *SND_RecvCommandReply(u32 flags);",
    "void SND_ReadDriverInfo(SndDriverInfo *info);",
    "BOOL SND_ReadChannelInfo(const SndDriverInfo *driverInfo, int chNo, SNDChannelInfo *chInfo);",
    "BOOL SND_ReadTrackInfo(const SndDriverInfo *driverInfo, int playerNo, int trackNo, SNDTrackInfo *trackInfo);",
    "u16 SND_GetChannelStatus(void);", "int SND_GetPlayerLocalVariable(u32 playerNo, int varNo);",
    "void SND_SetOutputSelector(s32 left, s32 right, s32 channel1, s32 channel3);",
    "void SND_SetupChannelPcm(s32 chNo, s32 format, const void *data, s32 loopMode, s32 loopStart, s32 dataLen, s32 volume, s32 shift, s32 timer, s32 pan);",
    "void SND_SetChannelVolume(u32 chBitMask, s32 volume, s32 shift);",
    "void SND_PrepareSeq(s32 playerNo, const void *seqBase, u32 seqOffset, void *bank);",
)
WAVE_DECLARATIONS = (
    "void SND_DestroyBank(void *bank);", "void SND_DestroyWaveArc(void *waveArc);",
    "u32 SND_GetWaveDataCount(const void *waveArc);", "const void *SND_GetWaveDataAddress(const void *waveArc, int index);",
    "void SND_SetWaveDataAddress(void *waveArc, int index, const void *waveData);",
    "SndInstPos SND_GetFirstInstDataPos(const void *bank);",
    "BOOL SND_GetNextInstData(const void *bank, SndInstData *instData, SndInstPos *instPos);",
)
# Exact counts guard the only native callback fields/signatures and pointer casts
# being widened. Serialized offsets and unrelated u32 fields stay untouched.
SOUND_FILES = {
    "lib/include/nnsys/snd_internal.h": (4, 0),
    "lib/include/nnsys/snd_arc_internal.h": (18, 0),
    "lib/include/nnsys/snd_arc_strm_internal.h": (2, 0),
    "lib/NitroSystem/src/snd_heap.c": (2, 0),
    "lib/NitroSystem/src/snd_arc.c": (6, 3),
    "lib/NitroSystem/src/snd_arc_loader.c": (2, 2),
    "lib/NitroSystem/src/snd_arc_loader_wave.c": (10, 1),
    "lib/NitroSystem/src/snd_player.c": (4, 0),
}


# Ownership is explicit; declarations and native layout come from original headers.
# This mechanism also supports future typed assembly BSS objects/member labels.
STORAGE = {
    "nnsys_g3d_snd_bss.s": (
        "gCurrentRenderState gGeBufferState gMatAnmResultBuffer gScaleCache gEvpMtxCache "
        "gSndMainState gSndDriverInfo gSndResourceMgr gSndWaveOuts "
        "gSndFreeSeqPlayerList gSndSeqPlayerPrioList gSndSeqPlayers gSndPlayerInfo "
        "gSndStrmListInitialized gSndStrmList gSndStrmCallbackBuffers "
        "gSndStrmChannels gSndCaptureWork gSndCurrentArc"),
    "nnsys_snd_arc_strm_bss.s": (
        "_021E0950 gSndArcStrmFreeCommandList gSndArcStrmMutex "
        "gSndArcStrmCommandList gSndArcStrmPlayers"),
    "nnsys_g2d_bss.s": (
        "gOamManagerNextId gOamBuffers gRendererWork gCellTransferStateManager "
        "gOamSoftEmuState gCurrentRndCore"),
}
STORAGE_ALIASES = {
    "gGeBufferStateIsLocked": ("gGeBufferState", "G3dGeBufferState", "isLocked"),
    "gScaleCacheScaleY": ("gScaleCache", "G3dScaleCacheEntry", "scale.y"),
    "gScaleCacheScaleZ": ("gScaleCache", "G3dScaleCacheEntry", "scale.z"),
    "gScaleCacheInvScale": ("gScaleCache", "G3dScaleCacheEntry", "invScale"),
    "gScaleCacheInvScaleY": ("gScaleCache", "G3dScaleCacheEntry", "invScale.y"),
    "gScaleCacheInvScaleZ": ("gScaleCache", "G3dScaleCacheEntry", "invScale.z"),
    "gEvpMtxCacheFirstDirMtx": ("gEvpMtxCache", "G3dEvpMtxCache", "dirMtx"),
    "gOamBufferMainOam": ("gOamBuffers", "OamManagerBuffer", "oamBuffer"),
    "gOamBufferMainAffineOwners": ("gOamBuffers", "OamManagerBuffer", "affineOwners"),
    "gOamBufferSubOamOwners": ("gOamBuffers", "OamManagerBuffer[3]", "[1].oamOwners"),
    "gOamBufferSubOam": ("gOamBuffers", "OamManagerBuffer[3]", "[1].oamBuffer"),
    "gOamBufferSubAffineOwners": ("gOamBuffers", "OamManagerBuffer[3]", "[1].affineOwners"),
    "gOamBufferSoftOamOwners": ("gOamBuffers", "OamManagerBuffer[3]", "[2].oamOwners"),
    "gOamBufferSoftOam": ("gOamBuffers", "OamManagerBuffer[3]", "[2].oamBuffer"),
    "gOamBufferSoftAffineOwners": ("gOamBuffers", "OamManagerBuffer[3]", "[2].affineOwners"),
    "gRendererZStack": ("gRendererWork", "G2dRendererWork", "zStack"),
    "gRendererMtxCacheRecords": ("gRendererWork", "G2dRendererWork", "mtxCacheRecords"),
    "_021D956C": ("gRendererWork", "G2dRendererWork", "mtxCacheRecords[0].state"),
    "gRendererMtxStack": ("gRendererWork", "G2dRendererWork", "mtxStack"),
    "gRendererMtxStackTransX": ("gRendererWork", "G2dRendererWork", "mtxStack[0]._20"),
    "gRendererMtxStackTransY": ("gRendererWork", "G2dRendererWork", "mtxStack[0]._21"),
    "gRendererAffineMtxStack": ("gRendererWork", "G2dRendererWork", "affineMtxStack"),
    "gRendererMtxCaches": ("gRendererWork", "G2dRendererWork", "mtxCaches"),
    "gRendererWorkB00": ("gRendererWork", "G2dRendererWork", "cellAnimMtxCaches"),
    "gRendererCellAnimMtxCaches": ("gRendererWork", "G2dRendererWork", "cellAnimMtxCaches"),
    "gRendererCellAnimMtxCacheTable": ("gRendererWork", "G2dRendererWork", "cellAnimMtxCaches.pCaches"),
    "gSndMainPreSleepCallback": ("gSndMainState", "SndMainState", "preSleep"),
    "gSndMainPostSleepCallback": ("gSndMainState", "SndMainState", "postSleep"),
    "gSndPlayerInfoNumPlaying": ("gSndPlayerInfo", "SndPlayerInfo", "playerList.numObjects"),
    "gSndPlayerInfoPlayableSeqCount": ("gSndPlayerInfo", "SndPlayerInfo", "playableSeqCount"),
    "gSndPlayerInfoAllocChBitFlag": ("gSndPlayerInfo", "SndPlayerInfo", "allocChBitFlag"),
    "gSndPlayerInfoVolume": ("gSndPlayerInfo", "SndPlayerInfo", "volume"),
    "gSndCaptureMsgQueue": ("gSndCaptureWork", "SndCaptureWork", "msgQueue"),
    "gSndCaptureState": ("gSndCaptureWork", "SndCaptureWork", "state"),
}


def native_storage(text, source):
    expected = {'nnsys_g3d_snd_bss.s': '9bbefd083d3f43888cea3a587035ae172a3244c5d68a9008717760fe4d69d86a', 'nnsys_snd_arc_strm_bss.s': '0dd6ff53f387e0ef77d942879f24ddbcf75e42ac4ad04d5e6bb5b0c809b58539'}
    expected['nnsys_g2d_bss.s'] = 'e7965b6eb25e8b0ac43c0e31a1f5f3b863cbb04a02696ebefc333f5c6c3388be'
    if hashlib.sha256(text.encode()).hexdigest() != expected[source.name]:
        raise ValueError("Original BSS ownership changed: " + source.name)
    manifest = (source.parent.parent.parent / "main.lsf").read_text()
    group = None
    membership = []
    for line in manifest.splitlines():
        match = re.match(r"^(Static|Overlay|Autoload)\s+(\w+)", line)
        if match:
            group = match.groups()
        if re.fullmatch(r"\s*Object lib/asm/" + re.escape(source.stem) + r"\.o\s*", line):
            membership.append(group)
    if membership != [("Static", "main")]:
        raise ValueError("Storage object absent from original static main image")
    owners = STORAGE[source.name].split()
    labels = dict(re.findall(r"^(\w+):\n\s*\.space (0x[0-9A-Fa-f]+)", text, re.M))
    headers = source.parent.parent / "include/nnsys"
    declarations = "\n".join((headers / name).read_text() for name in
        ("snd_internal.h", "snd_arc_internal.h", "snd_arc_strm_internal.h",
         "g2d_internal.h", "g2d_renderer_internal.h", "g3d_render_internal.h", "g3d_util_internal.h",
         "g3d_anm_mat_internal.h"))
    result = ('#include <stddef.h>\n#include <nnsys/snd_arc_strm_internal.h>\n'
              '#include <nnsys/g2d_renderer_internal.h>\n#include <nnsys/g3d_anm_mat_internal.h>\n')
    for name in owners:
        if name not in labels:
            raise ValueError("Missing original storage label: " + name)
        matches = re.findall(r"^extern ([^;\n]*\b" + re.escape(name)
                             + r"(?:\[[^\]]*\])?);", declarations, re.M)
        if name == 'gRendererWork': matches = ['G2dRendererWork gRendererWork']
        if len(matches) != 1:
            raise ValueError("Ambiguous original storage declaration: " + name)
        result += matches[0] + ";\n"
    aliases = [(name, spec) for name, spec in STORAGE_ALIASES.items() if spec[0] in owners]
    # Clang substitutes the compiler's offsetof constant into assembly. No ARM32
    # or hand-maintained numerical offsets enter Mach-O .set expressions.
    result += '__attribute__((used)) static void hg_storage_aliases(void) {\n'
    for name, (owner, ctype, member) in aliases:
        if name not in labels:
            raise ValueError("Missing original member label: " + name)
        offset = (f'offsetof({ctype}, {member})' if not member.startswith('[') else
                  f'(sizeof(OamManagerBuffer) * {member[1]} + offsetof(OamManagerBuffer, {member[4:]}))')
        if name=='gRendererWorkB00': offset += ' - offsetof(G2dRendererWorkB00, cellAnimIndex)'
        result += (f'    __asm__ volatile(".globl _{name}\\n.set _{name}, _{owner} + %c0"'
                   f' : : "i"({offset}));\n')
    result += '}\n'
    for view in ("U16", "U32", "U8"):
        result += (f'_Static_assert(sizeof(SndPlayerInfo{view}View) == sizeof(SndPlayerInfo), '
                   '"Native player alias stride");\n')
    return result


def nnsys_remaining_data(text):
    """Original main-owned scalar bytes and typed native dispatch/state records."""
    if hashlib.sha256(text.encode()).hexdigest() != '3976c18c03c1220c664dfc2a8ee353cbf9966252ef82efe76e9a7cc28c9983f7':
        raise ValueError('Original NitroSystem initializer data changed')
    blocks = {}
    current = None
    for line in text.splitlines():
        label = re.fullmatch(r'(\w+):', line)
        if label:
            current = label[1]; blocks[current] = []
        elif current and re.match(r'\s*\.(byte|word) ', line):
            blocks[current].append(line.strip())
    def words(name):
        return [v.strip() for line in blocks[name] for v in line.removeprefix('.word ').split(',')
                if line.startswith('.word ')]
    result = ('#include <stddef.h>\n#include <nnsys/fnd_internal.h>\n'
              '#include <nnsys/g2d_renderer_internal.h>\n#include <nnsys/g3d_internal.h>\n'
              '#include <nnsys/g3d_anm_internal.h>\n')
    def table(name, declaration, entries=None):
        nonlocal result
        values = words(name) if entries is None else entries
        result += declaration + ' = {' + ','.join('NULL' if v in ('0','0x00000000') else v for v in values) + '};\n'
    # All of these records contain only fixed-width numeric values. Preserve
    # their entire original bytes and member-label adjacency, including unused
    # tails and the billboard command blocks spanning labelled submatrices.
    numeric = '''gLnkTexVramSlotTable gG2dSoftSpriteCameraUp gG2dSoftSpriteCameraTarget
gObjHeights gObjWidths gCellTransferDstTypes gObjColorModeTexFmts gTexSizeInChars
gObjTexSizeS gObjTexSizeT gRndCoreIdentityMtx gCharShiftTable gObjShapeSizeAttrs
gMatColorMasks gPivotMtxIndices gJntAnmPivotMtxIndices gFrmTexVramRegions
gFrmTexVramRegion1 gFrmTexVramRegion2 _02110998 _021109B0
gRendererContext gRendererTranslationMtx gOamSoftEmuAutoZOffsetStep gAnmObjInitFuncCount
gTexGenTexImageCmds gPrjMapTexImageParam gEnvMapTexImageParam gPrjMapTexMtx
gBillboardCmd gBillboardCmdParams gBillboardMtx gBillboardTrans gBillboardScale
gBillboardYCmd gBillboardYCmdParams gBillboardYMtx gBillboardYTrans gBillboardYScale'''.split()
    public = set(re.findall(r'\.public\s+(\w+)', text))
    assembly = ['.section __DATA,__const', '.p2align 2']
    member_labels = set('''gFrmTexVramRegion1 gFrmTexVramRegion2 _02110998 _021109B0
gRendererTranslationMtx gPrjMapTexImageParam gEnvMapTexImageParam
gBillboardCmdParams gBillboardMtx gBillboardTrans gBillboardScale
gBillboardYCmdParams gBillboardYMtx gBillboardYTrans gBillboardYScale'''.split())
    for name in numeric:
        if any(not line.startswith('.byte ') for line in blocks[name]):
            raise ValueError('Numeric record gained a pointer: '+name)
        if name in {'gFrmTexVramRegions','gRendererContext','gTexGenTexImageCmds','gBillboardCmd','gBillboardYCmd'}:
            assembly += ['.section __DATA,__data', '.p2align 2']
        if name in public: assembly.append('.globl _'+name)
        if name in member_labels: assembly.append('.alt_entry _'+name)
        assembly += ['_'+name+':',*blocks[name]]
    import json
    result += '__asm__('+json.dumps('\n'.join(assembly)+'\n')+');\n'
    result += 'u16 gFrmTexVramSlotCount;\nFrmPlttVramManager gFrmPlttVramManager;\n'
    # Original four callbacks are two consecutive allocator records.
    allocators = words('gFndExpHeapAllocatorFunc')
    if len(allocators)!=4: raise ValueError('Allocator records changed')
    result += ('const NNSFndAllocatorFunc gFndExpHeapAllocatorFunc[2] = {{'+
               ','.join(allocators[:2])+'},{'+','.join(allocators[2:])+'}};\n')
    table('gVramTransferFuncTable', 'void (*const gVramTransferFuncTable[NNS_GFD_DST_MAX])(void *,u32,u32)')
    table('gOamLoadFuncs', 'OamLoadFunc gOamLoadFuncs[5]')
    for name,ctype in [('gAnmCalcFuncNsBva','G3dFuncAnmVis'),('gAnmCalcFuncNsBca','G3dFuncAnmJnt'),
                       ('gAnmCalcFuncNsBtp','G3dFuncAnmMat'),('gAnmCalcFuncNsBma','G3dFuncAnmMat'),
                       ('gAnmBlendVisDefault','NNSG3dFuncAnmBlendVis'),
                       ('gAnmBlendJntDefault','NNSG3dFuncAnmBlendJnt'),
                       ('gAnmBlendMatDefault','NNSG3dFuncAnmBlendMat')]:
        result += ctype+' '+name+' = '+words(name)[0]+';\n'
    for name,decl in [('gSendJointSRTFuncs','G3dFuncSendJointSRT gSendJointSRTFuncs[3]'),
                       ('gGetJointScaleFuncs','G3dFuncGetJointScale gGetJointScaleFuncs[3]'),
                       ('gSbcFuncs','void (*gSbcFuncs[32])(G3dRS *,u32)'),
                       ('gSbcMatFuncs','void (*gSbcMatFuncs[4])(G3dRS *,u32,const G3dResMatData *,u32)'),
                       ('gSbcShpFuncs','void (*gSbcShpFuncs[4])(G3dRS *,u32,const G3dResShpData *,u32)')]:
        if name in {'gSbcMatFuncs','gSbcShpFuncs'}:
            if blocks[name][1] != '.byte '+', '.join(['0x00']*12):
                raise ValueError('SBC NULL callbacks changed')
            table(name,decl,words(name)+['0']*3)
        else: table(name,decl)
    entries = []
    # The first category label and first-function label alias one table. Recover
    # all category bytes and authentic callbacks; ten original slots, five used.
    category = blocks['gAnmObjInitFuncs'][0]
    lines = blocks['gAnmObjInitFuncsFirstFunc']
    for i in range(5):
        raw = [int(v.strip(),0) for v in category.removeprefix('.byte ').split(',')]
        target = lines[i*2].removeprefix('.word ')
        entries.append('{%d,%d,%d,%s}' % (raw[0],raw[1],raw[2]|raw[3]<<8,target))
        if i<4: category = lines[i*2+1]
    result += 'G3dAnmObjInitEntry gAnmObjInitFuncs[10] = {'+','.join(entries)+'};\n'
    # SearchNormal aliases the final five elements of one seven-pointer array.
    # The original setter intentionally indexes through Search4x4[2..6].
    result += ('extern FrmTexVramRegion gFrmTexVramRegions[5];\n'
               'extern FrmTexVramRegion gFrmTexVramRegion1,gFrmTexVramRegion2;\n'
               'FrmTexVramRegion *gFrmTexVramSearch4x4[7] = {\n')
    indices = {'gFrmTexVramRegions':0,'gFrmTexVramRegion1':1,'gFrmTexVramRegion2':2,'_02110998':3,'_021109B0':4}
    result += ','.join('&gFrmTexVramRegions[%d]' % indices[n] for n in
                       words('gFrmTexVramSearch4x4')+words('gFrmTexVramSearchNormal'))+'};\n'
    result += '''__attribute__((used)) static void hg_nnsys_data_aliases(void) {
    __asm__ volatile(".globl _gAnmObjInitFuncsFirstFunc\\n.set _gAnmObjInitFuncsFirstFunc,_gAnmObjInitFuncs+%c0" : : "i"(offsetof(G3dAnmObjInitEntry,func)));
    __asm__ volatile(".globl _gFrmTexVramSearchNormal\\n.set _gFrmTexVramSearchNormal,_gFrmTexVramSearch4x4+%c0" : : "i"(2*sizeof(void *)));
}
_Static_assert(sizeof(G3dAnmObjInitEntry)==16,"native animation init stride");
_Static_assert(sizeof(FrmTexVramRegion)==24,"fixed VRAM numeric record");
_Static_assert(sizeof(G2dRendererContext)==32,"numeric renderer context and matrix");
'''
    return result


def asset_types(kind, text, source):
    if kind == 'native-card-spi-storage':
        if hashlib.sha256(text.encode()).hexdigest() != '5677a289072e2d843d96b1707a892efb0b78c0ea079585db9a996fd2193df9c7':
            raise ValueError('Original CARD SPI storage changed')
        return '''#include <nitro.h>
#include <nitro/card/card_spi_wait_internal.h>
CardSpiWait gCardSpiWait;
u8 gCardSpiCommand[0xBC];
u8 gCardSpiWriteCommand[0xC8];
u16 gCardSpiLockId = 0xFFFD;
_Static_assert(__builtin_offsetof(CardSpiWait,transfer.active) == 8, "native transfer alias");
_Static_assert(__builtin_offsetof(CardSpiWait,transfer.input) == 8 + __builtin_offsetof(CardSpiTransfer,input), "shared input");
_Static_assert(__builtin_offsetof(CardSpiWait,transfer.output) == 8 + __builtin_offsetof(CardSpiTransfer,output), "shared output");
_Static_assert(sizeof(CardSpiWait) == 8 + sizeof(CardSpiTransfer), "shared transfer extent");
__attribute__((used)) static void hg_card_spi_transfer_alias(void) {
    __asm__ volatile(".globl _gCardSpiTransfer\\n.set _gCardSpiTransfer,_gCardSpiWait+%c0" : : "i"(__builtin_offsetof(CardSpiWait,transfer.active)));
}
'''

    if kind == "guest-mi-memory":
        spec = importlib.util.spec_from_file_location("native_mi", Path(__file__).with_name("native_mi.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.translate(text, source)
    if kind == "native-mi-clear32":
        if (source.name != "mi_memory.c" or hashlib.sha256(text.encode()).hexdigest()
                != "7bfc34240ca43ec5c45773a7dad14547b0bb38fe7638c055a0f735e0aa0eb592"):
            raise ValueError("Original MI clear algorithm changed")
        # Direct translation of MIi_CpuClear32's ascending full-word stores.
        # This isolated boundary object does not override the SDK archive.
        return '''#include <stdint.h>
void MIi_CpuClear32(uint32_t data, void *destp, uint32_t size) {
    uint32_t *dest = destp;
    for (uint32_t offset = 0; offset < size; offset += 4)
        *dest++ = data;
}
'''
    if kind == "native-mi-clear-fast":
        if (source.name != "mi_memory.c" or hashlib.sha256(text.encode()).hexdigest()
                != "7bfc34240ca43ec5c45773a7dad14547b0bb38fe7638c055a0f735e0aa0eb592"):
            raise ValueError("Original MI clear algorithm changed")
        # MIi_CpuClearFast: eight ascending word stores per 32-byte block,
        # then individual word stores while the cursor is below the end.
        # Valid SDK inputs are word aligned and a multiple of four bytes.
        # Keep the original final full-word write for a partial trailing word.
        return '''#include <stdint.h>
void MIi_CpuClearFast(uint32_t data, void *destp, uint32_t size) {
    uint32_t *dest = destp;
    uint32_t blocks = size >> 5;
    while (blocks--) {
        dest[0] = data; dest[1] = data; dest[2] = data; dest[3] = data;
        dest[4] = data; dest[5] = data; dest[6] = data; dest[7] = data;
        dest += 8;
    }
    for (uint32_t tail = 0; tail < (size & 31); tail += 4)
        *dest++ = data;
}
'''
    if kind == "native-storage":
        return native_storage(text, source)
    if kind == "g3-probe-tables":
        # Native callback storage, not a widening of any serialized DS format.
        if source.name != "nnsys_data.s":
            raise ValueError("Unexpected G3 table source")
        checks = {
            "gSendTexSRTFuncs": "e5cc7f1c10901b32348b14127d509b202d65c7dc799480fa4a8280f86e95c726",
            "gTexMtxCalcFuncsMaya": "2406a076c144afc0a12a542f4f4e616d9f79e41e97903b9ab65a4f63f98188b1",
            "gTexMtxCalcFuncs3dsMax": "99d53c421528208c37ef65047a3e027b089f34d2f186fe256963a731f6da9803",
            "gTexMtxCalcFuncsXsi": "ad2a7a3edc79bed31c808428e684825cc3c83e43b11d01c66b2a49a7893f1ad6",
        }
        result = '#include <nnsys/g3d_anm_mat_internal.h>\n#include <nnsys/gfd_internal.h>\n'
        # Original main-owned runtime callback storage. Preserve Nintendo's
        # initial failure providers until an original VRAM manager installs its
        # own callbacks; these are native pointers, not serialized DS words.
        for name, ctype, provider in (
            ("NNS_GfdDefaultFuncAllocTexVram", "NNSGfdFuncAllocTexVram", "AllocTexVram_"),
            ("NNS_GfdDefaultFuncFreeTexVram", "NNSGfdFuncFreeTexVram", "FreeTexVram_"),
            ("NNS_GfdDefaultFuncAllocPlttVram", "NNSGfdFuncAllocPlttVram", "AllocPlttVram_"),
            ("NNS_GfdDefaultFuncFreePlttVram", "NNSGfdFuncFreePlttVram", "FreePlttVram_"),
        ):
            original = name + ':\n\t.word ' + provider + '\n'
            if text.count(original) != 1:
                raise ValueError("Original GFD callback initializer changed: " + name)
            result += f'{ctype} {name} = {provider};\n'
        # The original table declares const input, but XSI fills unused fields.
        # Its caller supplies mutable stack storage. Keep that behavior through
        # a type-correct native thunk rather than an incompatible indirect call.
        result += ('static void send_xsi(const G3dMatAnmResult *p) {\n'
                   '    NNSi_G3dSendTexSRTXsi((G3dMatAnmResult *)p);\n}\n')
        for name, digest in checks.items():
            matches = re.findall(r"^" + name + r":\n((?:\s*\.word [A-Za-z0-9_]+\n)+)", text, re.M)
            if len(matches) != 1 or hashlib.sha256(matches[0].encode()).hexdigest() != digest:
                raise ValueError("Original G3 dispatch table changed: " + name)
            entries = re.findall(r"\.word (\w+)", matches[0])
            ctype = "G3dFuncSendTexSRT" if name == "gSendTexSRTFuncs" else "G3dFuncTexMtxCalc"
            result += f'{ctype} {name}[{len(entries)}] = {{\n'
            result += ''.join('    ' + ('send_xsi' if e == 'NNSi_G3dSendTexSRTXsi' else e) + ',\n' for e in entries)
            result += '};\n'
        return result + '\n#ifdef HG_NATIVE_NNSYS_DATA\n' + nnsys_remaining_data(text) + '\n#endif\n'
    if kind == "zukan-enc-template":
        if (hashlib.sha256(text.encode()).hexdigest() != 'be5676e32c49f5c6a8a6e0bec069dc27fd0c2bcea00d8841bd69211ce35c139f'
                or hashlib.sha256(source.with_name("zukan_enc.mk").read_bytes()).hexdigest() != '9afc2fbd6ef49abbc21133674cf71a451565c1273bb4f9762e7efd86b5e34988'):
            raise ValueError("Original encounter asset recipe changed")
        return replace(text, ", @object", ", %object", count=3)
    if kind == "zukan-template":
        # In ARM assembler syntax @ begins a comment, so ELF object types use %.
        return replace(text, ", @object", ", %object", count=12)
    if kind == "ppark-types":
        declaration = span(text, "enum PalParkEncounterType {", "#define PPMONDAT_OFFSET_LAND_SECTOR")
        declaration = declaration[:declaration.rindex("#define PPMONDAT_OFFSET_LAND_SECTOR")]
        return ("typedef unsigned char u8;\n" + declaration
                + '_Static_assert(sizeof(struct PalParkMonsData) == 6, "DS Pal Park data");\n')
    if kind == "resdat-types":
        header = (source.parent / "sprite_resource_header.h").read_text()
        declarations = [
            span(text, "typedef enum GF_GraphicsResourceType {", "} GfGfxResType;"),
            span(text, "typedef struct GF_2DGfxResHeaderNarc {", "} GF_2DGfxResHeaderNarc;"),
            span(text, "typedef struct GF_2DGfxResHeaderNarcList {", "} GF_2DGfxResHeaderNarcList;"),
            span(header, "struct ResdatNarcEntry {", "};"),
        ]
        return ("typedef unsigned int u32;\ntypedef int BOOL;\n#define TRUE 1\n#define FALSE 0\n"
                + "\n".join(declarations)
                + '\n_Static_assert(sizeof(GfGfxResType) == 4 && sizeof(GF_2DGfxResHeaderNarc) == 24, "DS resource records");\n'
                + '_Static_assert(__builtin_offsetof(GF_2DGfxResHeaderNarcList, internal) == 4, "DS resource list");\n'
                + '_Static_assert(sizeof(struct ResdatNarcEntry) == 32, "DS resource entry");\n')
    if kind == "o2narc-reader":
        if hashlib.sha256(text.encode()).hexdigest() != "a98edd26a38234f4bf1000756568ebe1e4c0823786cff7b44bf5cbe85f7ba3a8":
            raise ValueError("Original ELF reader changed")
        start = text.index("void Elf::open(")
        end = text.index("Elf::~Elf()", start)
        return "#include <memory>\n#include <cstdint>\n" + text[:start] + ELF_OPEN + "\n" + text[end:]
    raise ValueError("Unknown asset adaptation kind: " + kind)


ELF_OPEN = """void Elf::open(const string &filename, ios::openmode openmode) {
    ELF_ASSERT(!handle.is_open() && strtab == nullptr && shstrtab == nullptr);
    handle.open(filename, openmode);
    ELF_ASSERT(handle.good());
    handle.seekg(0, ios::end);
    const streamoff file_size = handle.tellg();
    ELF_ASSERT(file_size >= static_cast<streamoff>(sizeof(Elf32_Ehdr)));
    handle.seekg(0);
    handle.read(reinterpret_cast<char *>(&ehdr), sizeof(ehdr));
    ELF_ASSERT(handle.good());
    ELF_ASSERT(memcmp(ehdr.e_ident, ELFMAG, SELFMAG) == 0);
    ELF_ASSERT(ehdr.e_ident[EI_CLASS] == ELFCLASS32);
    ELF_ASSERT(ehdr.e_ident[EI_DATA] == ELFDATA2LSB);
    ELF_ASSERT(ehdr.e_ident[EI_VERSION] == EV_CURRENT);
    ELF_ASSERT(ehdr.e_ehsize == sizeof(Elf32_Ehdr));
    ELF_ASSERT(ehdr.e_shentsize == sizeof(Elf32_Shdr));
    ELF_ASSERT(ehdr.e_shnum != 0 && ehdr.e_shstrndx < ehdr.e_shnum);
    ELF_ASSERT(uint64_t(ehdr.e_shoff) + uint64_t(ehdr.e_shnum) * sizeof(Elf32_Shdr) <= uint64_t(file_size));
    shdr.resize(ehdr.e_shnum);
    handle.seekg(ehdr.e_shoff);
    handle.read(reinterpret_cast<char *>(shdr.data()), shdr.size() * sizeof(Elf32_Shdr));
    ELF_ASSERT(handle.good());
    for (const auto &section : shdr) {
        if (section.sh_type != SHT_NOBITS)
            ELF_ASSERT(uint64_t(section.sh_offset) + section.sh_size <= uint64_t(file_size));
    }

    auto strings = [&](const Elf32_Shdr &section) {
        ELF_ASSERT(section.sh_type == SHT_STRTAB && section.sh_size != 0);
        std::unique_ptr<char[]> data(new char[section.sh_size]);
        handle.seekg(section.sh_offset);
        handle.read(data.get(), section.sh_size);
        ELF_ASSERT(handle.good());
        ELF_ASSERT(data[0] == 0 && data[section.sh_size - 1] == 0);
        return data;
    };
    const auto &section_strings = shdr[ehdr.e_shstrndx];
    auto section_names = strings(section_strings);
    const Elf32_Shdr *symbols = nullptr;
    for (const auto &section : shdr) {
        ELF_ASSERT(section.sh_name < section_strings.sh_size);
        ELF_ASSERT(memchr(section_names.get() + section.sh_name, 0, section_strings.sh_size - section.sh_name));
        if (section.sh_type == SHT_SYMTAB) {
            ELF_ASSERT(symbols == nullptr);
            symbols = &section;
        }
    }
    ELF_ASSERT(symbols != nullptr && symbols->sh_link < shdr.size());
    ELF_ASSERT(symbols->sh_entsize == sizeof(Elf32_Sym) && symbols->sh_size % sizeof(Elf32_Sym) == 0);
    const auto &symbol_strings = shdr[symbols->sh_link];
    // Even when both names use one ELF section, own two separate allocations:
    // the original Elf destructor independently deletes strtab and shstrtab.
    auto symbol_names = strings(symbol_strings);
    sym.resize(symbols->sh_size / sizeof(Elf32_Sym));
    handle.seekg(symbols->sh_offset);
    handle.read(reinterpret_cast<char *>(sym.data()), symbols->sh_size);
    ELF_ASSERT(handle.good());
    for (const auto &symbol : sym) {
        ELF_ASSERT(symbol.st_name < symbol_strings.sh_size);
        ELF_ASSERT(memchr(symbol_names.get() + symbol.st_name, 0, symbol_strings.sh_size - symbol.st_name));
        if (ELF32_ST_TYPE(symbol.st_info) == STT_OBJECT)
            ELF_ASSERT(symbol.st_shndx < shdr.size());
    }
    shstrtab = section_names.release();
    strtab = symbol_names.release();
}
"""


def write_if_changed(path, data):
    if path.exists() and path.read_text() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data)


def rc4_guest32(text):
    """Finite instruction elaboration of the original unrolled RC4 routine.

    Registers, flags, shifted indexing and store/load order stay explicit. This
    is not a replacement RC4 algorithm or a general guest instruction engine.
    """
    if hashlib.sha256(text.encode()).hexdigest()!='21c109973cd24847da150c828b013c28e261bbc9ecf6c8e660c89f35f6a115f2':
        raise ValueError('Original RC4 ARM source changed')
    match=re.search(r'asm void CRYPTO_RC4FastEncrypt\([^\n]*\) \{\n(.*?)\n\}',text,re.S)
    if not match:raise ValueError('Original RC4 function missing')
    body=['void CRYPTO_RC4FastEncrypt(void *context,const void *in,u32 length,void *out) {',
          'u32 r0=(u32)context,r1=(u32)in,r2=length,r3=(u32)out,r4=0,r5=0,r6=0,r7=0,r8=0,r9=0,lr=0;',
          'u32 x,y,z; int negative=0,zero=0,overflow=0;']
    def value(v):
        v=v.strip()
        if re.fullmatch(r'r[0-9]|lr',v):return v
        if re.fullmatch(r'#(?:0x[0-9a-f]+|[0-9]+)',v):return v[1:]+'u'
        if re.fullmatch(r'#-\d+',v):return '(-'+v[2:]+'u)'
        raise ValueError('Unsupported RC4 operand: '+v)
    def shifted(parts):
        if len(parts)==1:return value(parts[0])
        if len(parts)!=2:raise ValueError('RC4 shifted operand')
        m=re.fullmatch(r'(lsr|lsl) #(\d+)',parts[1])
        if not m or not 0<int(m[2])<32:raise ValueError('RC4 shift')
        return '('+value(parts[0])+(' >> ' if m[1]=='lsr' else ' << ')+m[2]+')'
    for raw in match[1].splitlines():
        line=raw.strip()
        if line.startswith('@') and line.endswith(':'):body.append(line[1:]);continue
        op,_,args=line.partition(' ')
        if (op,args)==('stmdb','sp!, {r4, r5, r6, r7, r8, r9, lr}'):
            statement='/* Native ABI preserves the original callee-save/return contract. */'
        elif (op,args)==('ldmia','sp!, {r4, r5, r6, r7, r8, r9, pc}'):statement='return;'
        elif op in ('bmi','bpl','ble','bgt'):
            if not re.fullmatch(r'@L[0-9A-F]+',args):raise ValueError('RC4 branch target')
            condition={'bmi':'negative','bpl':'!negative','ble':'zero || (negative!=overflow)','bgt':'!zero && (negative==overflow)'}[op]
            statement='if('+condition+')goto '+args[1:]+';'
        elif op in ('ldr','ldrb','str','strb'):
            m=re.fullmatch(r'(r\d+), \[(r\d+)(?:, (.*?))?\](?:, #(\d+))?',args)
            if not m:raise ValueError('RC4 memory instruction: '+line)
            reg,base,offset,post=m.groups();address=base+('+'+shifted(offset.split(', ')) if offset else '')
            pointer='((u8 *)('+address+'))' if op.endswith('b') else '((u32 *)('+address+'))'
            statement=reg+'=*'+pointer+';' if op.startswith('ldr') else '*'+pointer+'='+reg+';'
            if post:statement+=base+'+='+post+'u;'
        else:
            parts=args.split(', ')
            if op=='mov':statement=value(parts[0])+'='+shifted(parts[1:])+';'
            elif op in ('add','adds','sub','subs','eor','and'):
                dest=value(parts[0]);lhs=value(parts[1]);rhs=shifted(parts[2:]);symbol={'add':'+','adds':'+','sub':'-','subs':'-','eor':'^','and':'&'}[op]
                if op.endswith('s'):
                    statement='x='+lhs+';y='+rhs+';z=x'+symbol+'y;'+dest+'=z;zero=(z==0);negative=((int)z<0);'
                    statement+='overflow=((~(x^y)&(x^z))>>31)!=0;' if op=='adds' else 'overflow=(((x^y)&(x^z))>>31)!=0;'
                else:statement=dest+'='+lhs+symbol+rhs+';'
            else:raise ValueError('Unsupported original RC4 instruction: '+line)
        body.append(statement+' /* '+line+' */')
    body.append('}')
    return text[:match.start()]+'\n'.join(body)+text[match.end():]

def guest32_frontend(relative, text, root):
    """Source-validated frontend spelling/declaration corrections, still ARM32.

    No LP64 structure or algorithm adaptations are admitted to the guest input.
    Clang VFS keeps the original paths and ownership while these deterministic
    build-directory files repair mismatched declarations and finite ARM forms.
    """
    if relative == 'src/comm_state.c':
        return adapt(relative, text, root)
    if relative == 'src/comm_state_private.h':
        # Retain the original ARM32 MATHRandContext32 declaration. Its native
        # replacement header is an LP64 port detail, not a guest dependency.
        original=(root/'src/comm_state.c').read_text()
        private=set(re.findall(r'^static\s+(?:void|BOOL|s32|int)\s+(CommState_\w+)\(',original,re.M))
        if len(private)!=77:raise ValueError('CommState private helper definitions changed')
        for name in sorted(private):
            text,count=re.subn(r'^(?:void|BOOL|s32|int) '+name+r'\([^;\n]*;','',text,flags=re.M)
            if count!=1:raise ValueError('Private CommState declaration changed: '+name)
        return replace(text,'int DWC_Init(int);','int DWC_Init(void *work);')
    if relative == 'lib/include/nitro/os/thread.h':
        original = (root/'lib/NitroSDK/src/os/os_thread.c').read_text()
        if original.count('static void OSi_InsertLinkToQueue(OSThreadQueue *queue, OSThread *thread) {') != 1:
            raise ValueError('Original OS private queue helper changed')
        return drop(text, 'void OSi_InsertLinkToQueue(OSThreadQueue *queue, OSThread *thread);')
    if relative == 'lib/include/nitro/os/context.h':
        text=replace(text,'BOOL OS_SaveContext(register OSContext *context);',
                     '__attribute__((returns_twice)) BOOL OS_SaveContext(register OSContext *context);')
        return replace(text,'void OS_LoadContext(register OSContext *context);',
                       '__attribute__((noreturn)) void OS_LoadContext(register OSContext *context);')
    for source,name,lock in (('lib/NitroSDK/src/mic.c','MicWaitBusy','gMicLock'),
                             ('lib/NitroSDK/src/rtc/rtc_api.c','RtcWaitBusy','gRtcLock')):
        if relative==source:
            before=('asm void '+name+'(void) {\n    ldr r12, ='+lock+'\n@wait:\n'
                    '    ldr r0, [r12]\n    cmp r0, #1\n    beq @wait\n    bx lr\n}')
            after=('void '+name+'(void) {\n    /* Original ldr/cmp/beq loop; each read remains volatile. */\n'
                   '    while (*(volatile u32 *)&'+lock+' == 1) {}\n}')
            return replace(text,before,after)
    if relative == 'lib/src/nitrocrypto_rc4_fast.c':
        return rc4_guest32(text)
    spec = json.loads((Path(__file__).resolve().parents[1]/'compiler/guest32/sdk_asm_adaptations.json').read_text())
    for record in spec['adaptations']:
        if record['source'] != 'upstream/pokeheartgold/'+relative:
            continue
        if hashlib.sha256(text.encode()).hexdigest() != record['sha256']:
            raise ValueError('Original finite ARM adaptation source changed: '+relative)
        for replacement in record['replacements']:
            text = replace(text, replacement['original'], replacement['adapted'])
        if hashlib.sha256(text.encode()).hexdigest() != record['adapted_sha256']:
            raise ValueError('Finite ARM adaptation output changed: '+relative)
        return text
    raise ValueError('Unapproved guest32 frontend adaptation: '+relative)



def adapt_dwc_nas_native_allocation(text):
    """Adapt only the five original NAS allocation-size references."""
    changes = {
        "DWC_Alloc(4, 7712)": (1, "DWC_Alloc(4, sizeof(NetAuthWork))"),
        "MI_CpuFill8(allocated, 0, 7712)": (1, "MI_CpuFill8(allocated, 0, sizeof(NetAuthWork))"),
        "DWC_Free(4, gDwcNasLoginWork, 7712)": (3, "DWC_Free(4, gDwcNasLoginWork, sizeof(NetAuthWork))"),
    }
    for old, (expected, new) in changes.items():
        count = text.count(old)
        if count != expected:
            raise ValueError(
                f"NAS source contract changed: {old}: "
                f"expected {expected}, found {count}"
            )
        text = text.replace(old, new)
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-overlay-sources", action="store_true")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--kind", default="native")
    args = parser.parse_args()
    if args.list_overlay_sources:
        print(";".join(OVERLAY_NATIVE_SOURCES))
        return
    if args.root is None or args.input is None or args.output is None:
        parser.error("--root, --input and --output are required for generation")
    root, source = args.root.resolve(), args.input.resolve()
    source.relative_to(root)  # Every adaptation must come from the original tree.
    if args.output.resolve().is_relative_to(root):
        raise ValueError("Native outputs must not overwrite original upstream files")
    original = source.read_text()
    if args.kind == "native":
        relative = source.relative_to(root).as_posix()
        result = adapt(relative, original, root)
        if relative == "lib/NitroDWC/src/net_common.c":
            result = adapt_dwc_nas_native_allocation(result)
    elif args.kind == 'guest32-frontend':
        result = guest32_frontend(source.relative_to(root).as_posix(), original, root)
    elif args.kind == "coordinated-msl":
        result = coordinated.runtime_source(source.relative_to(root).as_posix(), original)
    else:
        result = asset_types(args.kind, original, source)
    write_if_changed(args.output, f'#line 1 {json.dumps(str(source), ensure_ascii=False)}\n' + result)


if __name__ == "__main__":
    main()
