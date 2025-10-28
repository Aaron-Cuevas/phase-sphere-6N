
#version 330 core
out vec4 FragColor;
uniform vec3 uColor;
void main(){
    // circular point
    vec2 c = gl_PointCoord*2.0-1.0;
    float r2 = dot(c,c);
    if(r2>1.0) discard;
    FragColor = vec4(uColor, 0.9);
}
