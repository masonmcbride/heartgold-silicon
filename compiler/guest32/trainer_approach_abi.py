"""Validate the pinned trainer task ABI before guest32 virtual-source publication."""

def adapt(relative, text):
    if str(relative) != "src/scrcmd_battle.c":
        return text
    for fragment in (
        "SysTask **approachTask;",
        "if (TrainerApproach_IsDone(*approachTask) == TRUE) {",
        "if (*approachTask == NULL) {",
        "TrainerApproach_Delete(*approachTask);",
    ):
        expected = 2 if fragment == "SysTask **approachTask;" else 1
        if text.count(fragment) != expected:
            raise ValueError("Original task lifecycle drift: " + fragment)
    return text


def adapt_public_header(text):
    before = "BOOL TrainerApproach_IsDone(SysTask *task);"
    if text.count(before) != 1:
        raise ValueError("Original trainer public prototype drift")
    return text
