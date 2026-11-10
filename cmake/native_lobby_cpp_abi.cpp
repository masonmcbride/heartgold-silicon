// Native ARM64 ABI boundary for original OVY_45 C++ identities.
// Original guest32 binaries and member ownership remain unchanged.
#include <stdexcept>

// Original C implementations, already compiled into OVY_45.
extern "C" void *LobbyCharVector_Destroy(void *);
extern "C" void *LobbyEventDeque_Destroy2(void *);

// The original alias maps establish:
// Bytes::~Bytes() -> LobbyCharVector_Destroy (offset 0)
// Deque::~Deque() -> LobbyEventDeque_Destroy2 (offset 0)
//
// VecStorage is Bytes' first and only member. Its original source
// requires LobbyCharVector_Destroy. These entry points must not
// invoke each other: each invocation destroys its argument once.

extern "C" void HG_Bytes_D1(void *)
    __asm__("__ZN5BytesD1Ev");
extern "C" void HG_VecStorage_D1(void *)
    __asm__("__ZN10VecStorageD1Ev");
extern "C" void HG_Deque_D1(void *)
    __asm__("__ZN5DequeD1Ev");

extern "C" void HG_Bytes_D1(void *self) {
    LobbyCharVector_Destroy(self);
}

extern "C" void HG_VecStorage_D1(void *self) {
    LobbyCharVector_Destroy(self);
}

extern "C" void HG_Deque_D1(void *self) {
    LobbyEventDeque_Destroy2(self);
}

// Original Metrowerks implementation throws a length_error with
// this exact message. Use the native C++ exception representation.
extern "C" [[noreturn]] void HG_VectorThrowLengthError()
    __asm__("__ZNSt15__vector_commonILb1EE18throw_length_errorEv");

extern "C" [[noreturn]] void HG_VectorThrowLengthError() {
    throw std::length_error("vector length error");
}
