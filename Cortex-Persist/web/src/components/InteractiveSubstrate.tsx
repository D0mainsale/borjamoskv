import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { KeyboardControls } from '@react-three/drei';
import { Physics } from '@react-three/rapier';
// @ts-ignore
import { EffectComposer, Bloom, Noise, Vignette } from '@react-three/postprocessing';
import Experience from './three/Experience';
import { useStrategy } from '../contexts/StrategyContext';

// Keyboard mapping for Cyber-rover
const map = [
  { name: 'forward', keys: ['ArrowUp', 'KeyW'] },
  { name: 'backward', keys: ['ArrowDown', 'KeyS'] },
  { name: 'left', keys: ['ArrowLeft', 'KeyA'] },
  { name: 'right', keys: ['ArrowRight', 'KeyD'] },
  { name: 'jump', keys: ['Space'] },
  { name: 'boost', keys: ['ShiftLeft', 'ShiftRight'] },
];

interface InteractiveSubstrateProps {
  isFrontierMode?: boolean;
}

export const InteractiveSubstrate: React.FC<InteractiveSubstrateProps> = ({ isFrontierMode }) => {
  const strategy = useStrategy();

  return (
    <div className="interactive-substrate-container">
      <KeyboardControls map={map}>
        <Canvas
          camera={{ 
            position: isFrontierMode ? [0, 0, 80] : [0, 15, 30], 
            fov: isFrontierMode ? 70 : 40 
          }}
          dpr={[1, 2]}
          gl={{ antialias: true, alpha: true }}
        >
          <color attach="background" args={['#050505']} />
          <Suspense fallback={null}>
            <Physics gravity={[0, -9.81, 0]}>
              <Experience 
                measuredEntropy={strategy.measuredEntropy}
                exergyLevel={strategy.exergyLevel}
                factCount={strategy.factCount}
                isArchiLoading={strategy.isArchiLoading}
                isFrontierMode={isFrontierMode}
              />
            </Physics>

            {/* Visual Depth Layer: Pure & Ethereal */}
            <EffectComposer enableNormalPass={false}>
              <Bloom 
                intensity={0.2} 
                luminanceThreshold={0.5} 
                mipmapBlur 
              />
              <Vignette eskil={false} offset={0.3} darkness={0.9} />
            </EffectComposer>
          </Suspense>
        </Canvas>
      </KeyboardControls>
    </div>
  );
};
