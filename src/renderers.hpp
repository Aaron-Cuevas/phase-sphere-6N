
#pragma once
#include <vector>
#include <glm/glm.hpp>
#include "shader.hpp"

struct GLPointCloud {
    unsigned vao=0, vbo=0;
    size_t count=0;
    void upload(const std::vector<glm::vec3>& pts);
    void draw() const;
    void destroy();
};

struct GLFrame {
    unsigned vao=0, vbo=0;
    void createAxes(float L=1.0f);
    void draw() const;
    void destroy();
};
