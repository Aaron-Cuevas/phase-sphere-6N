
#pragma once
#include <string>
#include <glad/gl.h>

struct ShaderProgram {
    GLuint id = 0;
    bool compileFromFiles(const std::string& vsPath, const std::string& fsPath);
    void use() const { glUseProgram(id); }
    void setMat4(const char* name, const float* value) const;
    void setFloat(const char* name, float v) const;
    void setInt(const char* name, int v) const;
    void setVec3(const char* name, float x, float y, float z) const;
    void destroy();
};
