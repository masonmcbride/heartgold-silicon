"""Original GameSpy B0 state: native ABI adaptation."""
import re

NSOCK = 'typedef struct NSockAddr {\n    u8 len;\n    u8 family;\n    u16 port;\n    u32 addr;\n} NSockAddr;'
ISTATE = 'typedef struct IState {\n    int state;      // 0x00\n    int sock;       // 0x04\n    NSockAddr addr; // 0x08\n    u8 buf[0x40];   // 0x10\n    int len;        // 0x50\n    u32 time;       // 0x54\n    int retries;    // 0x58\n} IState;'

def adapt(relative, text):
    if relative == "lib/NitroDWC/src/available_check_poll.c":
        # The polling TU already declares SockAddr before its work type.
        # Replace that declaration with the sender's NSockAddr ABI.
        pattern = r"typedef struct SockAddr\s*\{[^}]*\}\s*SockAddr\s*;"
        text, n = re.subn(
            pattern,
            lambda _: NSOCK + "\ntypedef NSockAddr SockAddr;",
            text, count=1
        )
        assert n == 1, "Polling SockAddr declaration changed"

        # One complete native owner, extracted from original ap_connect.c.
        pattern = (
            r"int ov00_0221B0D0;\s*"
            r"AvailableCheckWork ov00_0221B0D8;"
        )
        text, n = re.subn(
            pattern,
            lambda _: ISTATE + "\nIState ov00_0221B0D0;",
            text, count=1
        )
        assert n == 1, "Original B0 storage definitions changed"

        # Status-only original references become IState.state.
        decl = "IState ov00_0221B0D0;"
        assert text.count(decl) == 1
        before, after = text.split(decl, 1)
        after = re.sub(
            r"\bov00_0221B0D0\b(?!\s*\.)",
            "ov00_0221B0D0.state", after
        )
        text = before + decl + after

        # Poll and sender share time, retries and socket.
        text = text.replace(
            "ov00_0221B0D8.sendTime", "ov00_0221B0D0.time"
        )
        text = text.replace(
            "ov00_0221B0D8.retries", "ov00_0221B0D0.retries"
        )
        assert text.count("static int sNatSock;") == 1
        text = text.replace("static int sNatSock;", "", 1)
        text = re.sub(
            r"\bsNatSock\b", "ov00_0221B0D0.sock", text
        )

        assert text.count("typedef struct NSockAddr") == 1
        assert "typedef NSockAddr SockAddr;" in text
        assert "ov00_0221B0D0.state = 1;" in text
        assert "ov00_0221B0D0.sock" in text
        assert "ov00_0221B0D0.time" in text
        assert "ov00_0221B0D0.retries" in text
        return text

    if relative == "lib/NitroDWC/src/ap_connect.c":
        mapping = {
            "extern NSockAddr ov00_0221B0D8;":
                "#define ov00_0221B0D8 (ov00_0221B0D0.addr)",
            "extern u8 ov00_0221B0DC[];":
                "#define ov00_0221B0DC ((u8 *)&ov00_0221B0D0.addr.addr)",
            "extern u8 ov00_0221B0E0[];":
                "#define ov00_0221B0E0 (ov00_0221B0D0.buf)",
            "extern u8 ov00_0221B0E5[];":
                "#define ov00_0221B0E5 (ov00_0221B0D0.buf + 5)",
        }
        for old, new in mapping.items():
            assert text.count(old) == 1, f"Source drift: {old}"
            text = text.replace(old, new, 1)
        return text

    return text
