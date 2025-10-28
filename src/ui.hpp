
#pragma once
#include "phase_space.hpp"
#include <glm/glm.hpp>
#include <vector>

struct UIState {
    PhaseParams params;
    int ax_i=0, ax_j=1, ax_k=2;
    int proj_kind = 0; // 0 Axes, 1 Random, 2 PCA
    bool show_cells = false;
    bool show_frame = true;
    bool auto_resample = true;
};

void drawUI(UIState& S, int D, float R, double omega, double sigma, int pointCount);
