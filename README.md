# Phase-Sphere-6N — Microcanonical Hypersphere Visualizer (OpenGL)

Visualizador docente del **espacio de fase** en \(D=6N\) con muestreo microcanónico
sobre la cáscara \(H=E\), proyecciones 3D (Axes / Random / PCA) y panel ImGui.

## Build (CMake + FetchContent)
```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build . -j
./phase_sphere_6n.app/Contents/MacOS/phase_sphere_6n  # macOS
Controles
	•	Sliders: (N, m, E, \Delta).  Proyección: Axes/Random/PCA.
	•	Cámara: orbita con clic (configurable en main.cpp).
	•	Shaders: assets/shaders (carga relativa robusta).

Licencia

MIT.
