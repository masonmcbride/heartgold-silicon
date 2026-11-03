cmake_minimum_required(VERSION 3.24)
project(Guest32 LANGUAGES C CXX)
find_package(LLVM REQUIRED CONFIG)
if(NOT LLVM_VERSION_MAJOR EQUAL 23)
    message(FATAL_ERROR "guest32-lower requires LLVM 23")
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
add_executable(guest32-lower lower.cpp)
set_property(TARGET guest32-lower PROPERTY HG_LLVM_TOOLS_DIR "${LLVM_TOOLS_BINARY_DIR}")
target_compile_features(guest32-lower PRIVATE cxx_std_17)
target_include_directories(guest32-lower SYSTEM PRIVATE ${LLVM_INCLUDE_DIRS})
separate_arguments(guest32_definitions NATIVE_COMMAND "${LLVM_DEFINITIONS}")
target_compile_options(guest32-lower PRIVATE ${guest32_definitions})
llvm_map_components_to_libnames(guest32_libraries Core IRReader TransformUtils Analysis)
target_link_libraries(guest32-lower PRIVATE ${guest32_libraries})
enable_testing()
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
