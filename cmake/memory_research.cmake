# Observation of an existing original-engine executable; no engine replacement.
enable_language(OBJC)
add_library(hg_memory_observer SHARED "${PROJECT_SOURCE_DIR}/research/memory-pressure/memory_observer.c")
target_sources(hg_memory_observer PRIVATE "${PROJECT_SOURCE_DIR}/research/memory-pressure/memory_platform.m")
target_compile_definitions(hg_memory_observer PRIVATE HG_MEMORY_PLATFORM)
target_link_libraries(hg_memory_observer PRIVATE "-framework Foundation" "-framework Metal" "-framework IOKit")
add_executable(hg_memory_platform "${PROJECT_SOURCE_DIR}/research/memory-pressure/memory_platform.m")
target_compile_definitions(hg_memory_platform PRIVATE HG_PLATFORM_MAIN)
target_link_libraries(hg_memory_platform PRIVATE "-framework Foundation" "-framework Metal" "-framework IOKit")
set_target_properties(hg_memory_platform PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${PROJECT_BINARY_DIR}/memory-research")
set_target_properties(hg_memory_observer PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${PROJECT_BINARY_DIR}/memory-research")
add_executable(hg_memory_demand "${PROJECT_SOURCE_DIR}/research/memory-pressure/memory_demand.c")
set_target_properties(hg_memory_demand PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${PROJECT_BINARY_DIR}/memory-research")
target_compile_options(hg_memory_observer PRIVATE -Wall -Wextra)
target_compile_options(hg_memory_demand PRIVATE -Wall -Wextra)
find_package(Python3 3.9 REQUIRED COMPONENTS Interpreter)
add_test(NAME memory_research_metrics COMMAND "${Python3_EXECUTABLE}" -B
    "${PROJECT_SOURCE_DIR}/tests/test_memory_research.py" $<TARGET_FILE:hg_memory_demand>)
