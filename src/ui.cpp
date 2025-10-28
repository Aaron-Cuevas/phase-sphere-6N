
#include "ui.hpp"
#include "imgui.h"

void drawUI(UIState& S, int D, float R, double omega, double sigma, int pointCount){
    ImGui::Begin("Microcanon - 6N");
    ImGui::Text("D = %d = 6N", D);
    ImGui::SliderInt("N (particles)", &S.params.N, 1, 64);
    ImGui::SliderFloat("mass m", &S.params.m, 0.1f, 10.0f, "%.3f", ImGuiSliderFlags_Logarithmic);
    ImGui::SliderFloat("energy E", &S.params.E, 0.05f, 50.0f, "%.3f", ImGuiSliderFlags_Logarithmic);
    ImGui::SliderFloat("shell Δ (rel)", &S.params.shell, 0.001f, 0.2f, "%.4f", 0);
    ImGui::SliderInt("samples", &S.params.samples, 1000, 200000);
    ImGui::Checkbox("auto resample", &S.auto_resample);
    ImGui::Separator();
    ImGui::Text("Projection");
    const char* kinds[]={"Axes (pick three)","Random proj","PCA (power iters)"};
    ImGui::Combo("kind", &S.proj_kind, kinds, IM_ARRAYSIZE(kinds));
    ImGui::InputInt("axis i", &S.ax_i); ImGui::SameLine(); ImGui::InputInt("axis j", &S.ax_j); ImGui::SameLine(); ImGui::InputInt("axis k", &S.ax_k);
    ImGui::Checkbox("show microcells", &S.show_cells);
    ImGui::Checkbox("show frame", &S.show_frame);
    ImGui::Separator();
    ImGui::Text("R = sqrt(2 m E) = %.4f", R);
    ImGui::Text("omega_D(R) ≈ %.4e", omega);
    ImGui::Text("sigma_{D-1}(R) ≈ %.4e", sigma);
    ImGui::Text("points: %d", pointCount);
    ImGui::End();
}
