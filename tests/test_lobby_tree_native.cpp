using Node = TreeEraseRebalance::Node;
static_assert(sizeof(u32) == 4, "Nintendo word width must match the native game build");
#define PREFIX(T, field) \
    static_assert(offsetof(T, field) == 2 * sizeof(void *), "tagged parent offset"); \
    static_assert(alignof(T) >= 2, "parent low bit is available"); \
    static_assert(sizeof(((T *)0)->field) == sizeof(uintptr_t), "parent width")
PREFIX(LobbyUserIdSetNode, parent);
PREFIX(LobbyUserMapNode, parent);
PREFIX(LobbyChannelMapNode, parent);
PREFIX(PPWLobbyPlayerSetNode, parent);
PREFIX(TreeIterator::TreeNode, parent);
PREFIX(TreeInsertRebalance::Node, parent);
PREFIX(TreeEraseRebalance::Node, tagged);
PREFIX(TreeNode, parent);
static_assert(sizeof(EnterMainChannel::Channel) == sizeof(PPWLobbyChannel), "canonical channel size");
static_assert(alignof(EnterMainChannel::Channel) == alignof(PPWLobbyChannel), "channel alignment");
static_assert(offsetof(EnterMainChannel::Channel, storage) == offsetof(PPWLobbyChannel, name), "channel name offset");
static_assert(offsetof(EnterMainChannel::Channel, usersEnumerated) == offsetof(PPWLobbyChannel, usersEnumerated), "channel flags offset");
struct Item : Node { int key; };
static Node *nativeParent(Node *n) { return (Node *)(n->tagged & ~(uintptr_t)1); }
static int verify(Node *n, Node *p, int lo, int hi, int &count) {
    if (!n) return 1;
    assert(nativeParent(n) == p);
    int k = static_cast<Item *>(n)->key;
    assert(lo < k && k < hi);
    if (n->tagged & 1) {
        assert(!n->left || !(n->left->tagged & 1));
        assert(!n->right || !(n->right->tagged & 1));
    }
    ++count;
    int left = verify(n->left, n, lo, k, count);
    int right = verify(n->right, n, k, hi, count);
    assert(left == right);
    return left + !(n->tagged & 1);
}
static void check(Node *sentinel, int expected) {
    Node *root = sentinel->left;
    assert(!root || !(root->tagged & 1));
    int count = 0;
    verify(root, sentinel, -1, 10000, count);
    assert(count == expected);
    if (!root) return;
    Node *first = root;
    while (first->left) first = first->left;
    Iterator it = {first};
    int last = -1, traversed = 0;
    while (it.current != sentinel) {
        Item *n = static_cast<Item *>(it.current);
        assert(last < n->key);
        last = n->key;
        ++traversed;
        assert(traversed <= expected);
        TreeIterator::LobbyTreeIterator_Advance(&it);
    }
    assert(traversed == expected);
}
static unsigned allocations, frees;
extern "C" {
char gLobbyStr_TreeInsertLengthError_2[] = "tree length overflow";
void *LobbyMem_Alloc(u32 size) {
    assert(size == sizeof(PPWLobbyPlayerSetNode));
    void *p = malloc(size);
    assert(p && (uintptr_t)p > UINT32_MAX);
    // A narrow parent write must not accidentally pass using zeroed padding.
    memset(p, 0xa5, size);
    ++allocations;
    return p;
}
void DWC_Free(int heap, void *p, u32 size) {
    assert(heap == 0 && p && size == 0);
    ++frees;
    free(p);
}
}
static void player_set_lifetime() {
    PPWLobbyPlayer players[128] = {};
    for (unsigned trial = 0; trial < 8; ++trial) {
        PPWLobbyPlayerSet set = {};
        auto *sentinel = reinterpret_cast<PPWLobbyPlayerSetNode *>(&set.root);
        set.leftmost = sentinel;
        unsigned minimum = 128;
        for (unsigned i = 0; i < 128; ++i) {
            unsigned key = (i * 73 + trial * 17) % 128;
            PPWLobbyPlayer *player = players + key;
            player->id = key;
            PPWLobbyPlayerSetNode *parent;
            u8 left, leftmost;
            auto *position = PPWLobbyPlayerSet_FindInsertPos(&set, &player, &parent, &left, &leftmost);
            auto *node = PPWLobbyPlayerSet_InsertNode(&set, position, left, leftmost, &player);
            assert(node->player == player && set.count == i + 1);
            if (key < minimum) minimum = key;
            assert(set.leftmost->player->id == (int)minimum);
            // Traverse the C-produced objects through the actual C++ iterator.
            Iterator it = {set.leftmost};
            int last = -1;
            unsigned count = 0;
            while (it.current != sentinel) {
                auto *current = static_cast<PPWLobbyPlayerSetNode *>(it.current);
                assert(current->player->id > last);
                last = current->player->id;
                assert(++count <= set.count);
                TreeIterator::LobbyTreeIterator_Advance(&it);
            }
            assert(count == set.count);
            assert((set.root->parent & ~(uintptr_t)1) == (uintptr_t)sentinel);
            assert(!(set.root->parent & 1));
        }
        assert(PPWLobbyPlayerSet_Destroy(&set) == &set);
        assert(allocations == frees);
        // The original destructor owns nodes only; never reuse dangling links.
        set = {};
        for (unsigned i = 0; i < 128; ++i) assert(players[i].id == (int)i);
    }
}
int main() {
    player_set_lifetime();
    // Real heap addresses on this ARM64 host are above the DS address range.
    Item *nodes = new Item[128]();
    assert((uintptr_t)nodes > UINT32_MAX);
    struct GuardedChannel {
        uint64_t before;
        EnterMainChannel::Channel channel;
        uint64_t after;
    } guarded;
    guarded.before = guarded.after = UINT64_C(0x12345678abcdef01);
    guarded.channel.usersEnumerated = TRUE;
    guarded.channel.modeReady = FALSE;
    guarded.channel.name().str.l.isLong = 1;
    guarded.channel.name().str.l.ptr = reinterpret_cast<char *>(nodes);
    assert(guarded.channel.name().str.l.ptr == reinterpret_cast<char *>(nodes));
    assert(guarded.channel.usersEnumerated == TRUE && guarded.channel.modeReady == FALSE);
    assert(guarded.before == guarded.after && guarded.after == UINT64_C(0x12345678abcdef01));
    for (unsigned trial = 0; trial < 8; ++trial) {
        Node sentinel = {};
        for (unsigned i = 0; i < 128; ++i) {
            unsigned key = (i * 73 + trial * 17) % 128;
            Item *n = nodes + key;
            n->left = n->right = nullptr;
            n->key = key;
            Node *up = &sentinel;
            Node **link = &sentinel.left;
            while (*link) {
                up = *link;
                link = key < (unsigned)static_cast<Item *>(up)->key ? &up->left : &up->right;
            }
            n->tagged = (uintptr_t)up;
            *link = n;
            TreeInsertRebalance::LobbyTree_InsertRebalance(n, sentinel.left);
            check(&sentinel, i + 1);
        }
        // Remove ascending keys: successor traversal, leaf and one-child cases,
        // rotations, recolouring, root removal and the end sentinel.
        for (int i = 0; i < 128; ++i) {
            int key = trial & 1 ? (i * 53 + 31) % 128 : i;
            TreeEraseRebalance::LobbyTree_EraseRebalance(nodes + key, sentinel.left);
            check(&sentinel, 127 - i);
        }
    }
    delete[] nodes;
}
