static void split(bool chat, const char *input, const char *delimiter, int max,
                  std::vector<std::string> expected) {
    Str s, d;
    LobbyString_InitFromCStr(&s, input);
    LobbyString_InitFromCStr(&d, delimiter);
    struct Guarded { uintptr_t before; LobbyStringVector v; uintptr_t after; } out;
    out.before = 0x123456789abcdef0ULL; out.after = ~out.before;
    if (chat) LobbyChat_SplitString(&out.v, &s, &d, max);
    else LobbyString_Split(&out.v, &s, &d, max);
    assert(out.before == 0x123456789abcdef0ULL && out.after == ~out.before);
    assert(out.v.size == expected.size());
    for (u32 i = 0; i < out.v.size; i++) {
        assert(out.v.data[i].c_str() == expected[i]);
        if (out.v.data[i].l.isLong) {
            assert((uintptr_t)out.v.data[i].l.ptr > UINT32_MAX);
            assert(out.v.data[i].l.ptr != s.l.ptr);
        }
    }
    LobbyString_Destroy(&s); LobbyString_Destroy(&d);
    // Output owns independent copies after both inputs are destroyed.
    for (u32 i = 0; i < out.v.size; i++) assert(out.v.data[i].c_str() == expected[i]);
    LobbyStringVector_Destroy(&out.v);
    assert(live.empty());
}
int main() {
    static_assert(sizeof(Str) == 16, "native string");
    static_assert(sizeof(LobbyStringVector) == 16, "native vector");
    for (bool chat : {false, true}) {
        split(chat, "", ",", 0, {});
        split(chat, ",,a,,b,,", ",", 0, {"a", "b"});
        split(chat, "a,b,c", ",", 1, {"a,b,c"});
        split(chat, "a,b,c", ",", 2, {"a", "b,c"});
        split(chat, "a,b,c,d,e,f,g,h,i,j,k", ",", 0,
              {"a","b","c","d","e","f","g","h","i","j","k"});
        split(chat, "longer than ten characters,another long owned string", ",", 0,
              {"longer than ten characters", "another long owned string"});
    }
    split(false, "a:XbXYc", "XY", 0, {"a:Xb", "c"});
    split(true, "a:XbXYc", "XY", 0, {"a:", "b", "c"});
    // Empty character sets have no matches. Empty complete delimiters are not
    // exercised: the original algorithm does not advance on an empty delimiter.
    split(true, "abc", "", 0, {"abc"});
    puts("original native string/split ownership checks passed");
}
