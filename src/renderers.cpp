
#include "renderers.hpp"
#include <glad/gl.h>

void GLPointCloud::upload(const std::vector<glm::vec3>& pts){
    if(!vao){ glGenVertexArrays(1,&vao); glGenBuffers(1,&vbo); }
    glBindVertexArray(vao);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, pts.size()*sizeof(glm::vec3), pts.data(), GL_STATIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,sizeof(glm::vec3),(void*)0);
    glBindVertexArray(0);
    count = pts.size();
}
void GLPointCloud::draw() const{
    glBindVertexArray(vao);
    glDrawArrays(GL_POINTS, 0, (GLsizei)count);
    glBindVertexArray(0);
}
void GLPointCloud::destroy(){
    if(vbo){ glDeleteBuffers(1,&vbo); vbo=0; }
    if(vao){ glDeleteVertexArrays(1,&vao); vao=0; }
}

void GLFrame::createAxes(float L){
    if(!vao){ glGenVertexArrays(1,&vao); glGenBuffers(1,&vbo); }
    float lines[] = {
        0,0,0,  L,0,0,
        0,0,0,  0,L,0,
        0,0,0,  0,0,L
    };
    glBindVertexArray(vao);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(lines), lines, GL_STATIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,3*sizeof(float),(void*)0);
    glBindVertexArray(0);
}
void GLFrame::draw() const{
    glBindVertexArray(vao);
    glDrawArrays(GL_LINES, 0, 6);
    glBindVertexArray(0);
}
void GLFrame::destroy(){
    if(vbo){ glDeleteBuffers(1,&vbo); vbo=0; }
    if(vao){ glDeleteVertexArrays(1,&vao); vao=0; }
}
