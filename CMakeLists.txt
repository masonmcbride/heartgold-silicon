cmake_minimum_required(VERSION 3.30)
project(heartgold_silicon LANGUAGES C CXX)

# --- 1. Pinned repositories ---------------------------------------------------
set(HEARTGOLD_URL https://github.com/ctrl-cheeb-del/pokeheartgold.git)
set(HEARTGOLD_COMMIT 6d94f9137ced9db12d9ce827a8127c97b779bbeb)
set(LIBNTR_URL https://github.com/masonmcbride/libntr.git)
set(LIBNTR_COMMIT 4cfdd66fdca9a1f8f8e6688799f927c7fe3c3700)

# --- 2. Native Apple toolchain ------------------------------------------------
if(NOT APPLE OR NOT CMAKE_HOST_SYSTEM_PROCESSOR STREQUAL "arm64"
    OR NOT CMAKE_C_COMPILER_ID STREQUAL "AppleClang"
    OR NOT CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
    message(FATAL_ERROR "Use native Apple Clang on Apple Silicon")
endif()

set(CMAKE_OSX_ARCHITECTURES arm64)
find_package(Git REQUIRED)
file(MAKE_DIRECTORY "${PROJECT_SOURCE_DIR}/upstream")
find_library(COREFOUNDATION CoreFoundation REQUIRED)

# --- 3. Safe, offline-capable source checkouts ---------------------------------
function(dependency name url revision)
    set(source "${PROJECT_SOURCE_DIR}/upstream/${name}")
    set(head "")
    if(EXISTS "${source}")
        if(NOT EXISTS "${source}/.git")
            message(FATAL_ERROR "${source} is not a managed Git checkout; move it aside")
        endif()
        execute_process(
            COMMAND "${GIT_EXECUTABLE}" -C "${source}" rev-parse HEAD
            OUTPUT_VARIABLE head OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY
        )
        if(NOT head STREQUAL revision)
            execute_process(
                COMMAND "${GIT_EXECUTABLE}" -C "${source}" status --porcelain --untracked-files=all
                OUTPUT_VARIABLE dirty COMMAND_ERROR_IS_FATAL ANY
            )
            if(dirty)
                message(FATAL_ERROR "${source} has local changes. Commit or move them aside before changing its pin.")
            endif()
        endif()
    else()
        execute_process(
            COMMAND "${GIT_EXECUTABLE}" clone --no-checkout --no-tags --no-recurse-submodules "${url}" "${source}"
            RESULT_VARIABLE failed ERROR_VARIABLE error
        )
        if(failed)
            message(FATAL_ERROR "Cannot clone ${name} from ${url} (${failed}): ${error}. Check network access; existing checkouts are never recloned.")
        endif()
    endif()
    if(NOT head STREQUAL revision)
        execute_process(
            COMMAND "${GIT_EXECUTABLE}" -C "${source}" cat-file -e "${revision}^{commit}"
            RESULT_VARIABLE missing OUTPUT_QUIET ERROR_QUIET
        )
        if(missing)
            execute_process(
                COMMAND "${GIT_EXECUTABLE}" -C "${source}" fetch --no-tags --no-recurse-submodules "${url}" "${revision}"
                RESULT_VARIABLE failed ERROR_VARIABLE error
            )
            if(failed)
                message(FATAL_ERROR "Cannot fetch ${name} commit ${revision}: ${error}. Check the pin and network access; the working tree was not switched.")
            endif()
        endif()
        execute_process(
            COMMAND "${GIT_EXECUTABLE}" -C "${source}" checkout --no-overwrite-ignore --detach "${revision}"
            COMMAND_ERROR_IS_FATAL ANY
        )
    endif()
    execute_process(
        COMMAND "${GIT_EXECUTABLE}" -C "${source}" rev-parse HEAD
        OUTPUT_VARIABLE actual OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY
    )
    if(NOT actual STREQUAL revision)
        message(FATAL_ERROR "${name}: expected ${revision}, found ${actual}")
    endif()
    if(name STREQUAL "pokeheartgold" OR name STREQUAL "libntr")
        execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${source}" status --porcelain --untracked-files=all
            OUTPUT_VARIABLE dirty COMMAND_ERROR_IS_FATAL ANY)
        if(dirty)
            message(FATAL_ERROR "${name} must match its pinned commit with a clean working tree.")
        endif()
    endif()

endfunction()

dependency(pokeheartgold "${HEARTGOLD_URL}" "${HEARTGOLD_COMMIT}")
dependency(libntr "${LIBNTR_URL}" "${LIBNTR_COMMIT}")

# --- 4. Source roots ---------------------------------------------------------
set(game_source "${PROJECT_SOURCE_DIR}/upstream/pokeheartgold")
set(ntr_source "${PROJECT_SOURCE_DIR}/upstream/libntr")

# --- 5. Fixed-point constants: original C generator, libntr's pinned CSV --------
set(fx_tool "${game_source}/tools/gen_fx_consts")
add_executable(gen_fx_consts "${fx_tool}/main.c" "${fx_tool}/fx_data.c" "${fx_tool}/fx_encode.c")
target_compile_definitions(gen_fx_consts PRIVATE SOURCE_DIR="${ntr_source}/gen/nitro/fx"
    HG_GAME_REVISION="${HEARTGOLD_COMMIT}")
set(fx_header "${PROJECT_BINARY_DIR}/include/nitro/fx/fx_const.h")
add_custom_command(OUTPUT "${fx_header}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${PROJECT_BINARY_DIR}/include/nitro/fx"
    # The original tool derives its C guard from argv[1]; keep that path relative.
    COMMAND $<TARGET_FILE:gen_fx_consts> include/nitro/fx/fx_const.h
    DEPENDS gen_fx_consts "${ntr_source}/gen/nitro/fx/fx_const.csv"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
    VERBATIM)
add_custom_target(fx_constants DEPENDS "${fx_header}")

# --- 6. Native host services --------------------------------------------------
add_library(native_host STATIC hardware_drivers/os.c)
target_include_directories(native_host PUBLIC "${ntr_source}/include")
target_link_libraries(native_host PUBLIC "${COREFOUNDATION}")

add_library(nitro_config INTERFACE)
target_compile_features(nitro_config INTERFACE c_std_11)
target_compile_definitions(nitro_config INTERFACE
    SDK_PORT SDK_AARCH64 SDK_BUILD_MACOS SDK_64BIT SDK_VERSION_MAJOR=4
    HG_LIBNTR_REVISION="${LIBNTR_COMMIT}"
    SDK_CW_FORCE_EXPORT_SUPPORT SDK_TS SDK_4M SDK_FINALROM NNS_FINALROM _NITRO)
target_compile_options(nitro_config INTERFACE -fno-common)
target_include_directories(nitro_config INTERFACE "${ntr_source}/include" "${PROJECT_BINARY_DIR}/include")

# --- 7. Native SDK components (reuse pinned source manifests, not Meson) -------
function(ntr_library target)
    add_library(${target} STATIC ${ARGN})
    target_link_libraries(${target} PUBLIC nitro_config native_host)
    target_compile_options(${target} PRIVATE -include "${ntr_source}/include/pch/nitro_pch.h")
    add_dependencies(${target} fx_constants)
    set_target_properties(${target} PROPERTIES ARCHIVE_OUTPUT_DIRECTORY "${PROJECT_BINARY_DIR}/libntr")
endfunction()

add_library(nitro_sdk INTERFACE)
foreach(component os mi pxi ctrdg spi std card cp fx fs math dgt rtc gx snd)
    set(directory "${ntr_source}/libraries/${component}")
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${directory}/src/meson.build")
    file(READ "${directory}/src/meson.build" manifest)
    string(REGEX MATCH "lib${component}_srcs = files\\(([^)]*)\\)" declaration "${manifest}")
    if(NOT declaration)
        message(FATAL_ERROR "Source manifest changed for ${component}; inspect the pinned revision")
    endif()
    string(REGEX MATCH "if\\(sdk_version_major == 4\\)[ \t\r\n]*lib${component}_srcs \\+= files\\(([^)]*)\\)" additions "${manifest}")
    string(APPEND declaration "${additions}")
    string(REGEX MATCHALL "'[^']+\\.c'" names "${declaration}")
    set(sources)
    foreach(name IN LISTS names)
        string(REPLACE "'" "" name "${name}")
        list(APPEND sources "${directory}/src/${name}")
    endforeach()
    ntr_library(ntr_${component} ${sources})
    if(component STREQUAL "mi")
        target_sources(ntr_mi PRIVATE hardware_drivers/mi.c)
    endif()
    target_include_directories(ntr_${component} PRIVATE "${directory}/include")
    target_link_libraries(nitro_sdk INTERFACE ntr_${component})
endforeach()
ntr_library(ntr_sim_state
    "${ntr_source}/libraries/sim/src/sim_vars.c"
    "${ntr_source}/libraries/sim/src/sim_assert.c"
    "${ntr_source}/libraries/sim/src/queue.c"
    # Existing command decoding compiles without SDL; drawing remains unresolved.
    "${ntr_source}/libraries/sim/src/sim_g3_CommandProcessor.cpp"
    "${ntr_source}/libraries/sim7/src/pxi.c")
target_compile_features(ntr_sim_state PRIVATE cxx_std_17)
target_include_directories(ntr_sim_state PRIVATE "${ntr_source}/libraries/sim7/include")
target_link_libraries(nitro_sdk INTERFACE ntr_sim_state)
target_link_options(nitro_sdk INTERFACE -Wl,-dead_strip)

# --- 8. SDK correctness tests ------------------------------------------------
enable_testing()
add_executable(test_sdk_interfaces tests/test_sdk_interfaces.c)
target_link_libraries(test_sdk_interfaces PRIVATE nitro_sdk)
target_compile_options(test_sdk_interfaces PRIVATE -UNDEBUG)
add_test(NAME sdk_interfaces COMMAND test_sdk_interfaces)
add_executable(test_qsort tests/test_qsort.c)
target_link_libraries(test_qsort PRIVATE ntr_math)
target_compile_options(test_qsort PRIVATE -UNDEBUG)
add_test(NAME native_qsort COMMAND test_qsort)
find_package(Python3 3.9 REQUIRED COMPONENTS Interpreter)
add_test(NAME native_qsort_adaptations COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_native_qsort.py")
add_executable(test_os tests/test_os.c)
target_link_libraries(test_os PRIVATE nitro_sdk)
add_test(NAME os_init COMMAND test_os)
set_tests_properties(os_init PROPERTIES TIMEOUT 10)
add_executable(test_host tests/test_host.c)
target_link_libraries(test_host PRIVATE native_host)
add_test(NAME native_host COMMAND test_host)
set_tests_properties(native_host PROPERTIES TIMEOUT 10)
add_executable(test_heap EXCLUDE_FROM_ALL tests/test_heap.c
    "${game_source}/lib/NitroSystem/src/fnd_expheap.c"
    "${game_source}/lib/NitroSystem/src/fnd_heapcommon.c"
    "${game_source}/lib/NitroSystem/src/fnd_list.c")
target_link_libraries(test_heap PRIVATE nitro_sdk)
target_compile_options(test_heap PRIVATE "-idirafter${game_source}/lib/include"
    -fsanitize=address,undefined -fno-sanitize-recover=all)
target_link_options(test_heap PRIVATE -fsanitize=address,undefined)
add_dependencies(test_heap fx_constants)
add_test(NAME nitrosystem_heap COMMAND test_heap)
# Unmodified Nintendo heap metadata truncates native pointers. Keep the test,
# but do not execute it or claim support until that upstream-only constraint is resolved.
set_tests_properties(nitrosystem_heap PROPERTIES DISABLED TRUE)
add_executable(uncompress_reference "${game_source}/tools/asmdiff/ntruncompbw.c")
add_executable(test_uncompress tests/test_uncompress.c hardware_drivers/mi.c)
target_link_libraries(test_uncompress PRIVATE nitro_sdk)
target_compile_options(test_uncompress PRIVATE -O2 -fsanitize=address,undefined -fno-sanitize-recover=all)
target_link_options(test_uncompress PRIVATE -fsanitize=address,undefined)
add_dependencies(test_uncompress fx_constants)
add_test(NAME backward_decompression COMMAND test_uncompress $<TARGET_FILE:uncompress_reference>)
set_tests_properties(backward_decompression PROPERTIES TIMEOUT 20 ENVIRONMENT "ASAN_OPTIONS=detect_leaks=0")


# --- 9. Original HeartGold (default), with its native build adaptations --------
option(HEARTGOLD_BUILD_GAME "Build original HeartGold and its assets" ON)
if(HEARTGOLD_BUILD_GAME)
    find_package(Python3 3.9 REQUIRED COMPONENTS Interpreter)
    include("${CMAKE_CURRENT_LIST_DIR}/cmake/heartgold.cmake")
endif()

# Standalone emission observation only; never linked into heartgold.
option(HEARTGOLD_BUILD_G3_PROBE "Build the original NitroSystem emission probe" OFF)
if(HEARTGOLD_BUILD_G3_PROBE)
    find_package(Python3 3.9 REQUIRED COMPONENTS Interpreter)
    include("${CMAKE_CURRENT_LIST_DIR}/cmake/g3_probe.cmake")
endif()

option(HEARTGOLD_BUILD_MEMORY_RESEARCH "Build opt-in host memory observers" OFF)
if(HEARTGOLD_BUILD_MEMORY_RESEARCH)
    include("${CMAKE_CURRENT_LIST_DIR}/cmake/memory_research.cmake")
endif()
