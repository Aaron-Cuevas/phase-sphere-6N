
#include "samplers.hpp"
#include <cmath>
#include <algorithm>

static float sampleRadiusShell(std::mt19937& rng, float R, float rel, int D){
    // r in [R(1-Δ), R(1+Δ)] with PDF ∝ r^{D-1}  => use inverse CDF of r^D
    float a = std::max(0.0001f, R*(1.0f - rel));
    float b = R*(1.0f + rel);
    std::uniform_real_distribution<float> U(0.0f, 1.0f);
    float u = U(rng);
    float aD = std::pow(a, (float)D);
    float bD = std::pow(b, (float)D);
    float rD = aD + (bD - aD) * u;
    return std::pow(rD, 1.0f / (float)D);
}

std::vector<float> sampleMicrocanonicalShell(const PhaseParams& P){
    int D = dimensionD(P.N);
    int count = P.samples;
    std::vector<float> data((size_t)count * (size_t)D);
    std::mt19937 rng(P.seed);
    std::normal_distribution<float> N01(0.0f, 1.0f);

    float R = energyRadius(P);

    for(int s=0; s<count; ++s){
        // Direction ~ normalized Gaussian vector in R^D
        std::vector<float> v(D);
        double norm2 = 0.0;
        for(int d=0; d<D; ++d){ float g = N01(rng); v[d]=g; norm2 += (double)g*g; }
        float inv = 1.0f / std::sqrt((float)norm2 + 1e-12f);

        float r = sampleRadiusShell(rng, R, P.shell, D);

        for(int d=0; d<D; ++d){
            data[(size_t)s*(size_t)D + (size_t)d] = r * v[d] * inv;
        }
    }
    return data;
}

float cellSizeHint(const PhaseParams& P){
    // crude: let "microcell" edge diminish with D and R, just for visualization
    float R = energyRadius(P);
    int D = dimensionD(P.N);
    return 0.015f * R * std::pow(3.0f/(float)D, 0.5f);
}
