
#include <cstdio>
#include <vector>
#include <string>
#include <cmath>

#include <glad/gl.h>
#include <GLFW/glfw3.h>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <filesystem>

#include "imgui.h"
#include "backends/imgui_impl_glfw.h"
#include "backends/imgui_impl_opengl3.h"

#include "shader.hpp"
#include "renderers.hpp"
#include "phase_space.hpp"
#include "samplers.hpp"
#include "projection.hpp"
#include "ui.hpp"

static void glfwErrorCb(int code, const char* desc){ std::fprintf(stderr,"GLFW %d: %s\n", code, desc); }

int main(int argc, char** argv){
    glfwSetErrorCallback(glfwErrorCb);
    if(!glfwInit()){ return 1; }
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR,3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR,3);
    glfwWindowHint(GLFW_OPENGL_PROFILE,GLFW_OPENGL_CORE_PROFILE);
#ifdef __APPLE__
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
#endif
    GLFWwindow* win = glfwCreateWindow(1280, 800, "Phase space 6N — microcanonical shell", nullptr, nullptr);
    if(!win){ glfwTerminate(); return 2; }
    glfwMakeContextCurrent(win);
    glfwSwapInterval(1);

    if(gladLoadGL(glfwGetProcAddress)==0){ std::fprintf(stderr,"Failed to load GL\n"); return 3; }
    glEnable(GL_PROGRAM_POINT_SIZE);

    // ImGui
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO(); (void)io;
    ImGui::StyleColorsDark();
    ImGui_ImplGlfw_InitForOpenGL(win, true);
    ImGui_ImplOpenGL3_Init("#version 330 core");

    // Shaders
    ShaderProgram pointShader;
    pointShader.compileFromFiles("assets/shaders/point.vert", "assets/shaders/point.frag");
    ShaderProgram lineShader;
    lineShader.compileFromFiles("assets/shaders/line.vert", "assets/shaders/line.frag");

    GLPointCloud cloud;
    GLFrame frame; frame.createAxes(1.0f);

    UIState UI;
    std::vector<float> raw;
    std::vector<glm::vec3> pts;
    int D = dimensionD(UI.params.N);
    float R = energyRadius(UI.params);
    double omega = hypersphereVolume(D, R);
    double sigma = hypersurfaceArea(D, R);
    auto resample = [&](){
        D = dimensionD(UI.params.N);
        R = energyRadius(UI.params);
        omega = hypersphereVolume(D, R);
        sigma = hypersurfaceArea(D, R);
        raw = sampleMicrocanonicalShell(UI.params);
        ProjKind kind = (UI.proj_kind==0?ProjKind::Axes: UI.proj_kind==1?ProjKind::Random:ProjKind::PCA1);
        int ii = std::max(0, std::min(D-1, UI.ax_i));
        int jj = std::max(0, std::min(D-1, UI.ax_j));
        int kk = std::max(0, std::min(D-1, UI.ax_k));
        pts = project3D(raw, D, kind, ii, jj, kk, UI.params.seed+42);
        cloud.upload(pts);
    };
    resample();

    glm::vec3 camPos = glm::vec3(0,0,3.5f);
    float yaw=0, pitch=0;

    while(!glfwWindowShouldClose(win)){
        glfwPollEvents();
        int W,H; glfwGetFramebufferSize(win, &W,&H);
        glViewport(0,0,W,H);
        glClearColor(0.05f,0.06f,0.08f,1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        // glDisable(GL_DEPTH_TEST);

        // UI
        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();

        drawUI(UI, D, R, omega, sigma, (int)pts.size());
        if(UI.auto_resample){
            static PhaseParams prev = UI.params;
            static int prev_kind = UI.proj_kind;
            static int prev_i=-1, prev_j=-1, prev_k=-1;
            if( memcmp(&prev, &UI.params, sizeof(PhaseParams)) || prev_kind!=UI.proj_kind
                || prev_i!=UI.ax_i || prev_j!=UI.ax_j || prev_k!=UI.ax_k ){
                prev = UI.params; prev_kind = UI.proj_kind; prev_i=UI.ax_i; prev_j=UI.ax_j; prev_k=UI.ax_k;
                resample();
            }
        }

        // Camera (simple orbit with mouse-right drag)
        if(glfwGetMouseButton(win, GLFW_MOUSE_BUTTON_LEFT)==GLFW_PRESS){
            static double px=-1, py=-1; double x,y; glfwGetCursorPos(win,&x,&y);
            if(px>=0){ yaw += float(x-px)*0.005f; pitch += float(y-py)*0.005f; }
            px=x; py=y;
        }else{
            // reset stored
        }
        camPos = glm::vec3(4.5f*std::cos(yaw)*std::cos(pitch),
                           4.5f*std::sin(pitch),
                           4.5f*std::sin(yaw)*std::cos(pitch));

        glm::mat4 P = glm::perspective(glm::radians(45.0f), float(W)/float(H), 0.01f, 100.0f);
        glm::mat4 V = glm::lookAt(camPos, glm::vec3(0,0,0), glm::vec3(0,1,0));
        glm::mat4 M = glm::mat4(1.0f);
        glm::mat4 MVP = P*V*M;

        // Frame axes
        if(UI.show_frame){
            lineShader.use();
            lineShader.setMat4("uMVP", &MVP[0][0]);
            lineShader.setVec3("uColor", 0.8f,0.8f,0.8f);
            glLineWidth(1.5f);
            frame.draw();
        }

        // Points
        pointShader.use();
        pointShader.setMat4("uMVP", &MVP[0][0]);
        pointShader.setFloat("uSize", 12.0f);
        pointShader.setVec3("uColor", 0.0f,1.0f,0.7f);
        cloud.draw();

        // ImGui render
        ImGui::Render();
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

        glfwSwapBuffers(win);
    }

    cloud.destroy(); frame.destroy();
    pointShader.destroy(); lineShader.destroy();
    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwDestroyWindow(win);
    glfwTerminate();
    return 0;
}
