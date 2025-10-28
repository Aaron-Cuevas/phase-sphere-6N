cmake_minimum_required(VERSION 3.20...3.31)
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)

project(PhaseSphere6N LANGUAGES C CXX)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
enable_language(C)

include(FetchContent)

# GLFW sin extras
set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
FetchContent_Declare(glfw GIT_REPOSITORY https://github.com/glfw/glfw.git GIT_TAG 3.3.9)
FetchContent_MakeAvailable(glfw)

# GLM
FetchContent_Declare(glm GIT_REPOSITORY https://github.com/g-truc/glm.git GIT_TAG 1.0.1)
FetchContent_MakeAvailable(glm)

# GLAD v2
FetchContent_Declare(glad GIT_REPOSITORY https://github.com/Dav1dde/glad.git GIT_TAG v2.0.6)
FetchContent_MakeAvailable(glad)
add_subdirectory(${glad_SOURCE_DIR}/cmake ${glad_BINARY_DIR})
glad_add_library(glad_gl_core_mx REPRODUCIBLE API gl:core=4.1)

# ImGui
FetchContent_Declare(imgui GIT_REPOSITORY https://github.com/ocornut/imgui.git GIT_TAG v1.91.0)
FetchContent_MakeAvailable(imgui)
set(IMGUI_SOURCES
  ${imgui_SOURCE_DIR}/imgui.cpp
  ${imgui_SOURCE_DIR}/imgui_draw.cpp
  ${imgui_SOURCE_DIR}/imgui_tables.cpp
  ${imgui_SOURCE_DIR}/imgui_widgets.cpp
  ${imgui_SOURCE_DIR}/backends/imgui_impl_glfw.cpp
  ${imgui_SOURCE_DIR}/backends/imgui_impl_opengl3.cpp
)

add_executable(phase_sphere_6n
  src/main.cpp
  src/shader.hpp
  src/shader.cpp
  src/renderers.hpp
  src/renderers.cpp        # <- ESTO FALTABA
  src/phase_space.hpp
  src/phase_space.cpp
  src/samplers.hpp
  src/samplers.cpp
  src/projection.hpp
  src/projection.cpp
  src/ui.hpp
  src/ui.cpp
  ${IMGUI_SOURCES}
)

target_include_directories(phase_sphere_6n PRIVATE
  ${imgui_SOURCE_DIR}
  ${imgui_SOURCE_DIR}/backends
  ${glad_SOURCE_DIR}/include     # para que imgui_impl_opengl3 vea <glad/gl.h>
)

# Haz que ImGui use GLAD como loader
target_compile_definitions(phase_sphere_6n PRIVATE IMGUI_IMPL_OPENGL_LOADER_GLAD)

# macOS: bundle y silenciar deprecations
if(APPLE)
  target_compile_definitions(phase_sphere_6n PRIVATE GL_SILENCE_DEPRECATION)
  set_target_properties(phase_sphere_6n PROPERTIES
    MACOSX_BUNDLE YES
    MACOSX_BUNDLE_GUI_IDENTIFIER "edu.sphere6n.demo"
  )
endif()

target_link_libraries(phase_sphere_6n PRIVATE
  glfw
  glad_gl_core_mx
  glm::glm
)

# Copiar assets al lado del binario/bundle
add_custom_command(TARGET phase_sphere_6n POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_directory
          ${CMAKE_SOURCE_DIR}/assets
          $<TARGET_FILE_DIR:phase_sphere_6n>/assets
)
