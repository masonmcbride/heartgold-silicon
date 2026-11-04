#include <nitro/types.h>

#include <nitro/code32.h>

#include "lobby_cpp_types.h"
#include "lobby_chat_manager.h"
#include <cstddef>

struct SetNode;

struct SetIt {
    SetNode *n;

    SetIt(SetNode *p)
        : n(p) {
    }
};

struct Iter8 {
    SetNode *n;
    u32 extra;

    Iter8(const SetIt &i)
        : n(i.n) {
    }
};
struct Vec;
extern "C" void LobbyU32Vector_AssignFromSet(Vec *, Iter8, Iter8, RangeTag);
extern "C" Vec *LobbyU32Vector_Destroy(Vec *);

struct VIt {
    int *p;

    VIt(int *q)
        : p(q) {
    }

    int &operator*() const {
        return *p;
    }

    VIt &operator++() {
        ++p;
        return *this;
    }
};

inline bool operator==(const VIt &a, const VIt &b) {
    return a.p == b.p;
}

inline bool operator!=(const VIt &a, const VIt &b) {
    return !(a == b);
}

struct Vec {
    int *ptr;
    u32 size, cap;

    Vec()
        : ptr(0)
        , size(0)
        , cap(0) {
    }

    void Build(SetIt f, SetIt l) {
        Init(f, l);
    }

    void Init(SetIt f, SetIt l) {
        Assign(f, l, AssignTag(), IteratorTag());
    }

    void Assign(SetIt f, SetIt l, const AssignTag &ta, const IteratorTag &tb) {
        Assign(Iter8(f), Iter8(l), ta, tb, RangeTag());
    }

    void Assign(Iter8 f, Iter8 l, const AssignTag &, const IteratorTag &, const RangeTag &td) {
        LobbyU32Vector_AssignFromSet(this, f, l, td);
    }

    void Destroy() {
        LobbyU32Vector_Destroy(this);
    }

    VIt begin() {
        return VIt(ptr);
    }

    VIt end() {
        return VIt(ptr + size);
    }
};

using MapNode = LobbyChannelMapNode;

using Root = LobbyChatManager;
typedef BOOL (*Method)(Root *, int);

struct MemberTable {
    u32 header[2];
    Method method;
};

extern "C" const MemberTable ov45_02255358;

static_assert(sizeof(MemberTable) == 16, "Native callback record size");
static_assert(offsetof(MemberTable, method) == 8, "Native callback offset");


struct Bound {
    Method m;
    Root *obj;

    Bound(Method mm, Root *o)
        : m(mm)
        , obj(o) {
    }

    void operator()(int v) const {
        (void)m(obj, v);
    }
};

template <class It, class F>
inline F ForEach(It first, It last, F f) {
    for (; first != last; ++first) {
        f(*first);
    }
    return f;
}

extern "C" BOOL LobbyChat_RemoveChannel(Root *root, Str *key);

extern "C" BOOL LobbyChat_RemoveChannel(Root *root, Str *key) {
    Iterator it;
    LobbyChannelMap_Find(&it, &root->channelMap, key);
    if (it.current == &root->channelMap.root) {
        return FALSE;
    }
    Vec values;
    LobbyUserIdSet *users = &static_cast<LobbyChannelMapNode *>(it.current)->entry.channel.users;
    values.Build(
        SetIt(reinterpret_cast<SetNode *>(users->first)),
        SetIt(reinterpret_cast<SetNode *>(&users->root))
    );
    LobbyChannelMap_EraseKey(&root->channelMap, key);
    ForEach(values.begin(), values.end(), Bound(ov45_02255358.method, root));
    values.Destroy();
    return TRUE;
}
