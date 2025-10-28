
#pragma once
#include <vector>
#include <cstddef>
#include <string>

struct PhaseParams {
    int N = 3;          // particles
    float m = 1.0f;     // mass (units)
    float E = 1.0f;     // total energy (kinetic-only demo)
    float shell = 0.02f; // relative half-thickness Δ such that r ∈ [R(1-Δ), R(1+Δ)]
    int samples = 20000;
    unsigned int seed = 1337;
    bool kinetic_only = true;
};

// D = 6N
int dimensionD(int N);

// Energy radius R = sqrt(2 m E) for kinetic-only toy Hamiltonian
float energyRadius(const PhaseParams& P);

// Hypersphere volume ω_D(R) = π^{D/2} R^D / Γ(D/2+1)
double hypersphereVolume(int D, double R);

// Hypersurface area σ_{D-1}(R) = d/dR ω_D(R) = 2 π^{D/2} R^{D-1} / Γ(D/2)
double hypersurfaceArea(int D, double R);

// Label helpers
std::string prettyLabelD(int D);
