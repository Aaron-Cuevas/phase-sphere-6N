
#include "phase_space.hpp"
#include <cmath>
#include <sstream>

int dimensionD(int N){ return 6*N; }

float energyRadius(const PhaseParams& P){
    return std::sqrt(2.0f * P.m * P.E);
}

double hypersphereVolume(int D, double R){
    return std::pow(M_PI, D/2.0) * std::pow(R, D) / std::tgamma(D/2.0 + 1.0);
}

double hypersurfaceArea(int D, double R){
    return 2.0 * std::pow(M_PI, D/2.0) * std::pow(R, D-1) / std::tgamma(D/2.0);
}

std::string prettyLabelD(int D){
    std::ostringstream ss; ss << D << " = 6N dims"; return ss.str();
}
