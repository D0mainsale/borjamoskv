import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface WebGLSubstrateProps {
  entropy?: number;      // 0.0 to 1.0 (complexity of the flow)
  equilibrium?: number;  // 0.0 to 1.0 (stability of particles)
  accentColor?: string;  // Hex color for the particles
}

/**
 * WebGLSubstrate — The Kinetic Foundation
 * Industrial Noir 2026 | C5-REAL Mathematical Flow
 */
export const WebGLSubstrate: React.FC<WebGLSubstrateProps> = ({
  entropy = 0.5,
  equilibrium = 0.5,
  accentColor = '#2BE58B'
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const requestRef = useRef<number>(null);
  const stateRef = useRef({
    entropy,
    equilibrium,
    accentColor
  });

  // Keep stateRef in sync with props without re-rendering the Three pipeline
  useEffect(() => {
    stateRef.current = { entropy, equilibrium, accentColor };
  }, [entropy, equilibrium, accentColor]);

  useEffect(() => {
    if (!mountRef.current) return;

    const width = window.innerWidth;
    const height = window.innerHeight;

    // 1. Scene Setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 5;

    const renderer = new THREE.WebGLRenderer({ 
      antialias: true, 
      alpha: true,
      powerPreference: 'high-performance'
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mountRef.current.appendChild(renderer.domElement);

    // 2. Geometry (BufferGeometry for Max Exergy)
    const particleCount = 5000;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const velocities = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 15;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 15;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 15;
      
      velocities[i * 3] = (Math.random() - 0.5) * 0.02;
      velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.02;
      velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.02;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    // 3. Material (Industrial Glow)
    const material = new THREE.PointsMaterial({
      color: new THREE.Color(accentColor),
      size: 0.015,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);

    // 4. Kinetic Loop
    let time = 0;
    const animate = () => {
      time += 0.005;
      const positions = geometry.attributes.position.array as Float32Array;
      const { entropy, equilibrium, accentColor: currentAccent } = stateRef.current;

      // Update material color if changed
      if (material.color.getHex() !== new THREE.Color(currentAccent).getHex()) {
        material.color.set(currentAccent);
      }

      for (let i = 0; i < particleCount; i++) {
        const idx = i * 3;
        
        // Mathematical Flow Field (Sinusoidal Interference)
        const x = positions[idx];
        const y = positions[idx + 1];
        
        const flowForceX = Math.sin(y * (2.0 + entropy * 2.0) + time) * 0.005;
        const flowForceY = Math.cos(x * (2.0 + entropy * 2.0) + time) * 0.005;

        // Apply forces with equilibrium dampening
        positions[idx] += flowForceX * (1.5 - equilibrium);
        positions[idx + 1] += flowForceY * (1.5 - equilibrium);
        
        // Subtle drift in Z
        positions[idx + 2] += Math.sin(time * 0.5 + x) * 0.002;

        // Boundary Check (Loop points)
        if (Math.abs(positions[idx]) > 8) positions[idx] *= -0.95;
        if (Math.abs(positions[idx + 1]) > 8) positions[idx + 1] *= -0.95;
      }

      geometry.attributes.position.needsUpdate = true;
      renderer.render(scene, camera);
      requestRef.current = requestAnimationFrame(animate);
    };

    animate();

    // 5. Cleanup
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
      renderer.dispose();
      geometry.dispose();
      material.dispose();
      if (mountRef.current) mountRef.current.removeChild(renderer.domElement);
    };
  }, []); // Setup once

  return (
    <div 
      ref={mountRef} 
      id="webgl-substrate"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: -2,
        pointerEvents: 'none',
        background: 'radial-gradient(circle at center, #0a0a0a 0%, #050505 100%)'
      }}
    />
  );
};
