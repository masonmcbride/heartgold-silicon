cmake_minimum_required(VERSION 3.24)
project(Guest32 LANGUAGES C CXX)
find_package(LLVM REQUIRED CONFIG)
if(NOT LLVM_VERSION_MAJOR EQUAL 23)
    message(FATAL_ERROR "guest32-lower requires LLVM 23")
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/rules.json")
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/rules.json" GUEST32_RULE_CATALOG)
configure_file(rules_catalog.h.in rules_catalog.h @ONLY)
add_executable(guest32-lower lower.cpp semantic_slots.cpp object_symbols.cpp)
target_include_directories(guest32-lower PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")
set_property(TARGET guest32-lower PROPERTY HG_LLVM_TOOLS_DIR "${LLVM_TOOLS_BINARY_DIR}")
target_compile_features(guest32-lower PRIVATE cxx_std_17)
# The supported game configuration leaves CMAKE_BUILD_TYPE unset. This is a
# production compiler, so that configuration must not run its analyses at -O0.
# Explicit Debug/Release configuration flags retain their normal meaning.
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    target_compile_options(guest32-lower PRIVATE -O2)
endif()
target_include_directories(guest32-lower SYSTEM PRIVATE ${LLVM_INCLUDE_DIRS})
separate_arguments(guest32_definitions NATIVE_COMMAND "${LLVM_DEFINITIONS}")
target_compile_options(guest32-lower PRIVATE ${guest32_definitions})
llvm_map_components_to_libnames(guest32_libraries Core IRReader TransformUtils Analysis Object)
target_link_libraries(guest32-lower PRIVATE ${guest32_libraries})
find_package(Clang REQUIRED CONFIG HINTS "${LLVM_INSTALL_PREFIX}/lib/cmake/clang")
add_executable(guest32-codegen codegen.cpp)
target_compile_features(guest32-codegen PRIVATE cxx_std_17)
target_include_directories(guest32-codegen SYSTEM PRIVATE ${LLVM_INCLUDE_DIRS} ${CLANG_INCLUDE_DIRS})
target_compile_options(guest32-codegen PRIVATE ${guest32_definitions})
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    target_compile_options(guest32-codegen PRIVATE -O2)
endif()
target_compile_definitions(guest32-codegen PRIVATE HG_CLANG_EXECUTABLE="${LLVM_TOOLS_BINARY_DIR}/clang")
target_link_libraries(guest32-codegen PRIVATE clang-cpp LLVM)
# Shared compiler libraries are explicit receipt inputs, not runtime discovery.
file(GENERATE OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/codegen-inputs.json" CONTENT
    "{\"version\":1,\"libraries\":[\"$<TARGET_FILE:clang-cpp>\",\"$<TARGET_FILE:LLVM>\"]}\n")
enable_testing()
add_test(NAME guest32_stable_ids COMMAND "${Python3_EXECUTABLE}" -B
    "${CMAKE_CURRENT_SOURCE_DIR}/../../tests/test_guest32_stable_ids.py")
add_test(NAME guest32_rule_model COMMAND "${Python3_EXECUTABLE}" -B
    "${CMAKE_CURRENT_SOURCE_DIR}/../../tests/test_guest32_rule_model.py"
    --build "${CMAKE_CURRENT_BINARY_DIR}" --lowerer "$<TARGET_FILE:guest32-lower>")
add_test(NAME guest32_regression COMMAND "${Python3_EXECUTABLE}" -B
    "${CMAKE_CURRENT_SOURCE_DIR}/../../tests/test_guest32_compiler.py"
    --build "${CMAKE_CURRENT_BINARY_DIR}"
    --llvm-config "${LLVM_TOOLS_BINARY_DIR}/llvm-config"
    --lowerer "$<TARGET_FILE:guest32-lower>")
set(GUEST32_GAME_BINARY_DIR "" CACHE PATH "Configured HeartGold binary directory for original-call regression")
if(GUEST32_GAME_BINARY_DIR)
    add_test(NAME guest32_bridge COMMAND "${Python3_EXECUTABLE}" -B
        "${CMAKE_CURRENT_SOURCE_DIR}/../../tests/test_guest32_bridge.py"
        --build "${CMAKE_CURRENT_BINARY_DIR}" --game-build "${GUEST32_GAME_BINARY_DIR}"
        --llvm-config "${LLVM_TOOLS_BINARY_DIR}/llvm-config" --lowerer "$<TARGET_FILE:guest32-lower>")
endif()
