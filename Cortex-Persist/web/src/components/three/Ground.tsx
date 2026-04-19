import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface GroundProps {
  entropy: number;
}

const Ground: React.FC<GroundProps> = ({ entropy }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  // Industrial Noir Grid Shader
  const shaderArgs = {
    uniforms: {
      uTime: { value: 0 },
      uColor: { value: new THREE.Color('#2B3BE5') },
      uEntropy: { value: 0 },
    },
    vertexShader: `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uTime;
      uniform vec3 uColor;
      uniform float uEntropy;
      varying vec2 vUv;

      void main() {
        vec2 grid = abs(fract(vUv * 50.0 - 0.5) - 0.5) / fwidth(vUv * 50.0);
        float line = min(grid.x, grid.y);
        float alpha = 1.0 - min(line, 1.0);
        
        // Entropy distortion
        float wave = sin(vUv.x * 10.0 + uTime * (1.0 + uEntropy * 5.0)) * 0.1 * uEntropy;
        
        vec3 color = mix(vec3(0.02), uColor, alpha * 0.3);
        gl_FragColor = vec4(color, 1.0);
      }
    `,
  };

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.getElapsedTime();
      materialRef.current.uniforms.uEntropy.value = entropy / 100;
    }
  });

  return (
    <mesh ref={meshRef} rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
      <planeGeometry args={[1000, 1000]} />
      <shaderMaterial
        ref={materialRef}
        attach="material"
        args={[shaderArgs]}
        transparent
      />
    </mesh>
  );
};

export default Ground;
