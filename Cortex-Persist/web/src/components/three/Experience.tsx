import React from 'react';
import { Environment, ContactShadows } from '@react-three/drei';
import Ground from './Ground';
import Agent from './Agent';
import Nodes from './Nodes';

interface ExperienceProps {
  measuredEntropy: number;
  exergyLevel: number;
  factCount: number;
  isArchiLoading: boolean;
  isFrontierMode?: boolean;
}

const Experience: React.FC<ExperienceProps> = ({ 
  measuredEntropy, 
  exergyLevel, 
  factCount,
  isArchiLoading,
  isFrontierMode
}) => {
  return (
    <>
      {/* Ethereal Lighting Protocol: Central Glow */}
      <ambientLight intensity={0.1} />
      <pointLight position={[0, 10, 0]} intensity={0.8} color="#fff" />
      
      {/* Strategic Entities */}
      {!isFrontierMode && <Agent exergyLevel={exergyLevel} />}
      <Nodes 
        measuredEntropy={measuredEntropy} 
        factCount={factCount} 
        isArchiLoading={isArchiLoading} 
        isFrontierMode={isFrontierMode}
      />
      
      {/* Substrate Ground: Hidden in deep space warp mode */}
      {!isFrontierMode && <Ground entropy={measuredEntropy} />}
      
      {/* Environment & Visual Polish */}
      <ContactShadows 
        position={[0, 0, 0]} 
        opacity={isFrontierMode ? 0 : 0.4} 
        scale={20} 
        blur={2} 
        far={4.5} 
      />
      <Environment preset={isFrontierMode ? "apartment" : "night"} />
    </>
  );
};

export default Experience;
