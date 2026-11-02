static unsigned calls;
static const u32 *expected_mode;
static void mode_callback(BOOL success, const char *channel, const u32 *mode, u32 param) {
    assert(success && std::string(channel) == "room");
    assert(mode == expected_mode && mode[7] == 20 && param == 73); ++calls;
}
static const char *const *expected_topics;
static const int *expected_counts;
static void channels_callback(BOOL success, u32 count, const char *const *channels,
                              const char *const *topics, const int *counts, u32 param) {
    assert(success && count == 37 && param == 89);
    assert(topics == expected_topics && counts == expected_counts);
    for (u32 i = 0; i < count; ++i) assert(std::string(channels[i]) == "room");
    ++calls;
}
static void entered(BOOL, int, const char *, u32) {}
static void keys(BOOL, const char *, int, const char *, const char *, u32) {}
static void users(BOOL, const char *, u32, void *, u32) {}
static void registration_types() {
    auto *r = NewHandler(&gLobbyRequestVtable, entered, 1);
    assert(r->callback.enterChannel == entered); LobbyRequest_Delete(r);
    r = NewHandler(&gLobbyRequestVtable, keys, 2);
    assert(r->callback.getChannelKeys == keys); LobbyRequest_Delete(r);
    r = NewHandler(&gLobbyRequestVtable, users, 3);
    assert(r->callback.enumUsers == users); LobbyRequest_Delete(r);
    assert(live.empty());
}
static void channel_name_lifetime() {
    for (const char *text : {"x", "a long native lobby base name with owned storage"}) {
        PPWLobbyWork work = {};
        LobbyString_InitFromCStr(&work.channelBaseName, text);
        PPWString base;
        PPWLobby_GetChannelBaseName(&base.str, &work);
        PPWString name = MakeMainChannelName(base);
        base.Destroy();
        LobbyString_Destroy(&work.channelBaseName);
        assert(std::string(name.CStr()) == std::string("main!") + text);
        name.Destroy();
        assert(live.empty());
    }
}
int main() {
    string_tests();
    registration_types();
    channel_name_lifetime();
    LobbyChatManager manager = {};
    gLobbyChatManager = &manager;
    LobbyString_InitFromCStr(&manager.channelPrefix, "prefix!");
    assert((uintptr_t)mode_callback > UINT32_MAX);
    assert((uintptr_t)channels_callback > UINT32_MAX);
    auto *r = NewHandler(&gLobbyRequestVtable, mode_callback, 73);
    assert((uintptr_t)r > UINT32_MAX && r->callback.getChannelMode == mode_callback);
    node.request = r;
    u32 *mode = (u32 *)LobbyMem_Alloc(8 * sizeof(u32));
    memset(mode, 0, 8 * sizeof(u32)); mode[7] = 20; expected_mode = mode;
    LobbyChat_OnGetChannelMode(nullptr, 0, "prefix!room", mode, r->id);
    assert(node.request == r && calls == 0); // Original unsuccessful response retains registration.
    LobbyChat_OnGetChannelMode(nullptr, 1, "prefix!room", mode, r->id);
    assert(!node.request && calls == 1);
    DWC_Free(0, mode, 0);
    const char **names = (const char **)LobbyMem_Alloc(37 * sizeof(char *));
    char *name = (char *)LobbyMem_Alloc(12); strcpy(name, "prefix!room");
    for (unsigned i = 0; i < 37; ++i) names[i] = name;
    const char *topics[] = {"topic"}; int counts[] = {20};
    expected_topics = topics; expected_counts = counts;
    for (unsigned repeat = 0; repeat < 4; ++repeat) {
        r = NewHandler(&gLobbyRequestVtable, channels_callback, 89);
        node.request = r;
        LobbyChat_OnEnumChannels(nullptr, 1, 37, names, topics, counts, r->id);
        assert(!node.request && calls == repeat + 2);
    }
    DWC_Free(0, name, 0); DWC_Free(0, names, 0);
    LobbyString_Destroy(&manager.channelPrefix);
    assert(live.empty());
    puts("native callback dispatch, pointer-array growth and teardown passed");
}
