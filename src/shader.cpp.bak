
#include "shader.hpp"
#include <fstream>
#include <sstream>
#include <vector>
#include <iostream>

static std::string readFile(const std::string& path){
    std::ifstream f(path, std::ios::binary);
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

bool ShaderProgram::compileFromFiles(const std::string& vsPath, const std::string& fsPath){
    std::string vsSrc = readFile(vsPath);
    std::string fsSrc = readFile(fsPath);
    const char* vsrc = vsSrc.c_str();
    const char* fsrc = fsSrc.c_str();

    GLuint vs = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vs, 1, &vsrc, nullptr);
    glCompileShader(vs);
    GLint ok = 0; glGetShaderiv(vs, GL_COMPILE_STATUS, &ok);
    if(!ok){
        GLint len=0; glGetShaderiv(vs, GL_INFO_LOG_LENGTH, &len);
        std::vector<char> log(len); glGetShaderInfoLog(vs, len, nullptr, log.data());
        std::cerr << "[VS] " << log.data() << std::endl; return false;
    }

    GLuint fs = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fs, 1, &fsrc, nullptr);
    glCompileShader(fs);
    glGetShaderiv(fs, GL_COMPILE_STATUS, &ok);
    if(!ok){
        GLint len=0; glGetShaderiv(fs, GL_INFO_LOG_LENGTH, &len);
        std::vector<char> log(len); glGetShaderInfoLog(fs, len, nullptr, log.data());
        std::cerr << "[FS] " << log.data() << std::endl; return false;
    }

    id = glCreateProgram();
    glAttachShader(id, vs); glAttachShader(id, fs);
    glLinkProgram(id);
    glDeleteShader(vs); glDeleteShader(fs);

    glGetProgramiv(id, GL_LINK_STATUS, &ok);
    if(!ok){
        GLint len=0; glGetProgramiv(id, GL_INFO_LOG_LENGTH, &len);
        std::vector<char> log(len); glGetProgramInfoLog(id, len, nullptr, log.data());
        std::cerr << "[LINK] " << log.data() << std::endl; return false;
    }
    return true;
}

void ShaderProgram::setMat4(const char* name, const float* v) const{
    GLint loc = glGetUniformLocation(id, name); glUniformMatrix4fv(loc, 1, GL_FALSE, v);
}
void ShaderProgram::setFloat(const char* name, float v) const{
    GLint loc = glGetUniformLocation(id, name); glUniform1f(loc, v);
}
void ShaderProgram::setInt(const char* name, int v) const{
    GLint loc = glGetUniformLocation(id, name); glUniform1i(loc, v);
}
void ShaderProgram::setVec3(const char* name, float x,float y,float z) const{
    GLint loc = glGetUniformLocation(id, name); glUniform3f(loc, x,y,z);
}
void ShaderProgram::destroy(){ if(id){ glDeleteProgram(id); id = 0; } }
