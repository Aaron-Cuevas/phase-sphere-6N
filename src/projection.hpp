
#pragma once
#include <vector>
#include <glm/glm.hpp>

enum class ProjKind { Axes, Random, PCA1 };

// Compute 3D positions from D-dim data (flat array length = count*D)
std::vector<glm::vec3> project3D(const std::vector<float>& data, int D, ProjKind kind,
                                 int ax_i, int ax_j, int ax_k, unsigned int seed = 1234);

// Rough PCA via power iterations to extract first three components
std::vector<glm::vec3> pcaProject3(const std::vector<float>& data, int D);
