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
COMPILER_NATIVE_SOURCES = tuple(SINIT_CALLBACKS) + (
    "src/application/pokedex/pokedex_main_seq.c", "src/field/weather_manager.c")


OVERLAY_NATIVE_SOURCES = tuple(path for path in LIBC_DECLARATIONS if not path.endswith(".h")) + ("src/wifi_setup/wifi_setup_share.c",) + tuple(QSORT_DECLARATIONS) + ("lib/NitroDWC/src/http_engine_request.c", "src/voice_chat.c") + tuple(PRIVATE_FUNCTIONS) + COMPILER_NATIVE_SOURCES
OVERLAY_NATIVE_SOURCES = tuple(dict.fromkeys(OVERLAY_NATIVE_SOURCES + tuple(p for p in coordinated.SOURCES if not p.endswith(".h"))))


def native_libc(relative, text):
    for declaration in LIBC_DECLARATIONS[relative]:
        text = drop(text, declaration)
    if relative == "src/lobby/ppw_lobby.cpp":
        text = replace(text, "using std::va_list;", "using ::va_list;")
    headers = '#include <stdio.h>\n#include <string.h>\n'
    if relative == "src/lobby/ppw_lobby.cpp":
        headers += '#include <cstring>\n'
    return headers + text


def adapt(relative, text, root):
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
        return '#include <nitro/spi/ARM9/mic.h>\n' + text
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


def adapt_original(relative, text, root):
    if relative == "lib/include/nnsys/g2d/g2d_CellTransferManager.h":
        return replace(text, "\nNNS_G2dInitCellTransferStateManager(", "\nint NNS_G2dInitCellTransferStateManager(")
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

        return "#include <stddef.h>\\n" + text
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
        return text
    if relative in ("lib/NitroSystem/src/gfd_vram_transfer_manager.c", "lib/NitroSystem/src/g3d_kernel.c"):
        names = ["GX_LoadTex", "GX_LoadTexPltt"]
        if relative.endswith("gfd_vram_transfer_manager.c"):
            names += ["GX_LoadClearImageColor", "GX_LoadClearImageDepth"]
        for name in names:
            text = replace(text, f"void {name}(void *src,", f"void {name}(const void *src,")
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
        "gSndMainState gSndDriverInfo gSndResourceMgr gSndWaveOuts "
        "gSndFreeSeqPlayerList gSndSeqPlayerPrioList gSndSeqPlayers gSndPlayerInfo "
        "gSndStrmListInitialized gSndStrmList gSndStrmCallbackBuffers "
        "gSndStrmChannels gSndCaptureWork gSndCurrentArc"),
    "nnsys_snd_arc_strm_bss.s": (
        "_021E0950 gSndArcStrmFreeCommandList gSndArcStrmMutex "
        "gSndArcStrmCommandList gSndArcStrmPlayers"),
}
STORAGE_ALIASES = {
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
        ("snd_internal.h", "snd_arc_internal.h", "snd_arc_strm_internal.h"))
    result = '#include <stddef.h>\n#include <nnsys/snd_arc_strm_internal.h>\n'
    for name in owners:
        if name not in labels:
            raise ValueError("Missing original storage label: " + name)
        matches = re.findall(r"^extern ([^;\n]*\b" + re.escape(name)
                             + r"(?:\[[^\]]*\])?);", declarations, re.M)
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
        result += (f'    __asm__ volatile(".globl _{name}\\n.set _{name}, _{owner} + %c0"'
                   f' : : "i"(offsetof({ctype}, {member})));\n')
    result += '}\n'
    for view in ("U16", "U32", "U8"):
        result += (f'_Static_assert(sizeof(SndPlayerInfo{view}View) == sizeof(SndPlayerInfo), '
                   '"Native player alias stride");\n')
    return result


def asset_types(kind, text, source):
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
        result = '#include <nnsys/g3d_anm_mat_internal.h>\n'
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
        return result
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
        result = adapt(source.relative_to(root).as_posix(), original, root)
    elif args.kind == "coordinated-msl":
        result = coordinated.runtime_source(source.relative_to(root).as_posix(), original)
    else:
        result = asset_types(args.kind, original, source)
    write_if_changed(args.output, f'#line 1 {json.dumps(str(source), ensure_ascii=False)}\n' + result)


if __name__ == "__main__":
    main()
