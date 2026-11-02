int main() {
    static_assert(offsetof(LobbyTimerMap, leftmost) - offsetof(LobbyTimerMap, root) == 2 * sizeof(void *), "native map header");
    static_assert(offsetof(LobbyTimerMapNode, id) == 3 * sizeof(void *), "native node prefix");
    assert((uintptr_t)zero_callback > UINT32_MAX);
    LobbyTimerMap map = {};
    auto *end = (LobbyTimerMapNode *)&map.root;
    map.leftmost = end;
    for (int cycle = 0; cycle < 4; ++cycle) {
        for (u32 i = 0; i < 64; ++i) {
            u32 id = i * 37 % 64;
            LobbyTimer timer = {100 - 7, 7, nullptr, OnEnterMainChannel::TimerForward<zero_callback>};
            LobbyTimerMapEntry entry;
            LobbyTimerMap_MakeEntry(&entry, id, &timer);
            Result r;
            LobbyTimerMap_Insert(&r, &map, &entry);
            assert(r.flag && r.node->id == id && (uintptr_t)r.node > UINT32_MAX);
            assert(r.node->timer.lastTime == 93 && r.node->timer.interval == 7 && !r.node->timer.param);
            LobbyTimerMap_Insert(&r, &map, &entry);
            assert(!r.flag && map.count == i + 1);
        }
        Iterator it = {map.leftmost};
        u32 id = 0;
        while (it.current != end) {
            auto *node = (LobbyTimerMapNode *)it.current;
            assert(node->id == id++);
            calls = 0;
            assert(Timer_Update(node, 100) && calls == 0); // strict original expiry
            assert(Timer_Update(node, 101) && calls == 1);
            assert(node->timer.lastTime == 101);
            assert(!Timer_Update(node, 109) && calls == 2);
            Iterator next;
            LobbyTimerMap_Erase(&next, &map, it);
            it = next;
        }
        assert(id == 64 && !map.count && !map.root && map.leftmost == end && live.empty());
    }
    for (u32 id = 0; id < 19; ++id) {
        LobbyTimer timer = {0, 1, nullptr, OnEnterMainChannel::TimerForward<zero_callback>};
        LobbyTimerMapEntry entry; LobbyTimerMap_MakeEntry(&entry, id, &timer);
        Result r; LobbyTimerMap_Insert(&r, &map, &entry);
    }
    LobbyTimerMap_Clear(&map);
    assert(!map.root && !map.count && map.leftmost == end && live.empty());
    struct Guard { uintptr_t a; ByteVector v; uintptr_t b; } guard;
    guard.a = guard.b = 0x123456789abcdef0ULL;
    for (u32 size : {1u, 17u, 4u, 257u, 0u}) {
        auto *bytes = (u8 *)malloc(size + 1);
        for (u32 i = 0; i < size; ++i) bytes[i] = i;
        guard.v.Assign(ByteIterator(bytes), ByteIterator(bytes + size));
        assert(guard.v.size == size && guard.v.capacity >= size);
        assert(!size || !memcmp(guard.v.data, bytes, size));
        if (size) assert((uintptr_t)guard.v.data > UINT32_MAX);
        assert(guard.a == guard.b && guard.a == 0x123456789abcdef0ULL);
        free(bytes);
    }
    guard.v.Destroy(); assert(live.empty());
    char *message = (char *)malloc(32);
    expected_message = message; expected_id = 73; calls = 0;
    PPWLobby_OnPlayerMessage(expected_id, message, &map);
    assert(calls == 1); free(message);
    puts("original timer insertion/duplicate/expiry/erasure and PPW forwarding passed");
}
