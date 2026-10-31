# Original files/msgdata/msg.mk escapes trainer names after JSONPROC.
if(NOT DEFINED INPUT OR NOT EXISTS "${INPUT}")
    message(FATAL_ERROR "Missing generated GMM: ${INPUT}")
endif()
file(READ "${INPUT}" contents)
string(REPLACE "&" "&amp;" contents "${contents}")
file(WRITE "${INPUT}" "${contents}")
