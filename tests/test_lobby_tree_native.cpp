using Node = TreeEraseRebalance::Node;
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
int main() {
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
