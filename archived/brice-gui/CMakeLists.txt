cmake_minimum_required(VERSION 3.16)
project(nabc_rov_control LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(nabc_rov
    src/main.cpp
)

target_include_directories(nabc_rov PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
