"""Guest32-only correction of reconstructed trainer-approach prototypes."""

def adapt(relative, text):
    if str(relative) != "src/scrcmd_battle.c":
        return text
    before = "if (TrainerApproach_IsDone() == TRUE) {"
    after = (
        "if (TrainerApproach_IsDone("
        "(void *)(uintptr_t)(*approachTask)) == TRUE) {"
    )
    for fragment in (
        before,
        "if (*approachTask == 0) {",
        "TrainerApproach_Delete(*approachTask);",
    ):
        if text.count(fragment) != 1:
            raise ValueError("Original task lifecycle drift: " + fragment)
    return '#include <stdint.h>\n' + text.replace(before, after)


def adapt_public_header(text):
    before = "BOOL TrainerApproach_IsDone(void);"
    if text.count(before) != 1:
        raise ValueError("Original trainer public prototype drift")
    return text.replace(
        before, "BOOL TrainerApproach_IsDone(void *task);"
    )
