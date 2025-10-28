
#pragma once
#include <vector>
#include <random>
#include "phase_space.hpp"

// Samples points on a D-dimensional thin shell with correct radial weighting (∝ r^{D-1}).
// Returns a flat array of size (count * D). Each point is split as q^{3N} | p^{3N}.
std::vector<float> sampleMicrocanonicalShell(const PhaseParams& P);

// Simple cube microcells in projected 3D: just returns per-point size hint in world units
float cellSizeHint(const PhaseParams& P);

// Projection helpers choose which indices go to XYZ (0..D-1)
struct AxisTriple { int i=0, j=1, k=2; };
