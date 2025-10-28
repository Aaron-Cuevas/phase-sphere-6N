
#include "projection.hpp"
#include <random>
#include <algorithm>
#include <numeric>
#include <cmath>

static std::vector<float> meanCenter(const std::vector<float>& x, int D){
    size_t n = x.size()/D;
    std::vector<float> mu(D,0);
    for(size_t i=0;i<n;++i)
        for(int d=0; d<D; ++d) mu[d] += x[i*D+d];
    for(int d=0; d<D; ++d) mu[d] /= float(n);

    std::vector<float> y(x);
    for(size_t i=0;i<n;++i)
        for(int d=0; d<D; ++d) y[i*D+d] -= mu[d];
    return y;
}

static void normalize(std::vector<float>& v){
    double n2=0; for(float a:v) n2+=a*a;
    float inv = 1.0f/std::sqrt((float)n2+1e-12f);
    for(float& a:v) a*=inv;
}

// y = X v  where X is (n x D), v is (D)
static std::vector<float> matVec(const std::vector<float>& X, int D, const std::vector<float>& v){
    size_t n = X.size()/D;
    std::vector<float> y(n,0);
    for(size_t i=0;i<n;++i){
        float acc=0;
        for(int d=0; d<D; ++d) acc += X[i*D+d]*v[d];
        y[i]=acc;
    }
    return y;
}

// Xᵗ y
static std::vector<float> matTvec(const std::vector<float>& X, int D, const std::vector<float>& y){
    size_t n = X.size()/D;
    std::vector<float> v(D,0);
    for(int d=0; d<D; ++d){
        double acc=0;
        for(size_t i=0;i<n;++i) acc += X[i*D+d]*y[i];
        v[d]=(float)acc;
    }
    return v;
}

std::vector<glm::vec3> pcaProject3(const std::vector<float>& data, int D){
    auto X = meanCenter(data, D);
    std::mt19937 rng(777);
    std::uniform_real_distribution<float> U(-1,1);

    auto power = [&](int iters){
        std::vector<float> v(D); for(int d=0; d<D; ++d) v[d]=U(rng);
        normalize(v);
        for(int k=0;k<iters;++k){
            auto y = matVec(X,D,v);            // y = X v
            auto w = matTvec(X,D,y);           // w = Xᵗ y  ≈ (XᵗX) v
            normalize(w); v.swap(w);
        }
        return v;
    };

    // First component
    auto v1 = power(20);
    // Deflate
    auto y1 = matVec(X,D,v1);
    for(size_t i=0;i<y1.size();++i)
        for(int d=0; d<D; ++d) X[i*D+d] -= y1[i]*v1[d];

    // Second
    auto v2 = power(20);
    auto y2 = matVec(X,D,v2);
    for(size_t i=0;i<y2.size();++i)
        for(int d=0; d<D; ++d) X[i*D+d] -= y2[i]*v2[d];

    // Third
    auto v3 = power(20);

    size_t n = data.size()/D;
    std::vector<glm::vec3> out(n);
    auto X0 = meanCenter(data,D);
    for(size_t i=0;i<n;++i){
        float a=0,b=0,c=0;
        for(int d=0; d<D; ++d){
            float xi = X0[i*D+d];
            a+=xi*v1[d]; b+=xi*v2[d]; c+=xi*v3[d];
        }
        out[i] = {a,b,c};
    }
    return out;
}

std::vector<glm::vec3> project3D(const std::vector<float>& data, int D, ProjKind kind,
                                 int ax_i, int ax_j, int ax_k, unsigned int seed){
    size_t n = data.size()/D;
    std::vector<glm::vec3> out(n);

    if(kind==ProjKind::Axes){
        for(size_t i=0;i<n;++i){
            out[i] = { data[i*D+ax_i], data[i*D+ax_j], data[i*D+ax_k] };
        }
        return out;
    }else if(kind==ProjKind::PCA1){
        return pcaProject3(data, D);
    }else{
        // Random Gaussian projection (Johnson–Lindenstrauss style)
        std::mt19937 rng(seed);
        std::normal_distribution<float> N01(0.0f,1.0f);
        std::vector<float> R(3*D);
        for(int k=0;k<3*D;++k) R[k]=N01(rng);
        // Normalize rows
        for(int r=0;r<3;++r){
            double n2=0; for(int d=0;d<D;++d) n2+=R[r*D+d]*R[r*D+d];
            float inv = 1.0f/std::sqrt((float)n2+1e-12f);
            for(int d=0;d<D;++d) R[r*D+d]*=inv;
        }
        for(size_t i=0;i<n;++i){
            float x=0,y=0,z=0;
            for(int d=0;d<D;++d){
                float v = data[i*D+d];
                x += v*R[0*D+d];
                y += v*R[1*D+d];
                z += v*R[2*D+d];
            }
            out[i] = {x,y,z};
        }
        return out;
    }
}
