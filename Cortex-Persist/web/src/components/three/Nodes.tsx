import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { RigidBody, CuboidCollider } from '@react-three/rapier';
import { Html } from '@react-three/drei';
import * as THREE from 'three';
import { useStrategy } from '../../contexts/StrategyContext';
import { sonic } from '../../utils/SonicService';

interface NodesProps {
  measuredEntropy: number;
  factCount: number;
  isArchiLoading: boolean;
  isFrontierMode?: boolean;
}

const Nodes: React.FC<NodesProps> = ({ measuredEntropy, factCount, isArchiLoading, isFrontierMode }) => {
  const { setProximityNode, proximityNode, hechosSoberanos } = useStrategy();

  const nodes = useMemo(() => {
    if (isFrontierMode) {
      // STARFIELD MODE: 50+ nodes in a tunnel/field configuration
      return Array.from({ length: 150 }).map((_, i) => ({
        id: `star-${i}`,
        position: [
          (Math.random() - 0.5) * 100,
          (Math.random() - 0.5) * 100,
          (Math.random() - 1) * 200, // Depth
        ],
        label: '',
        color: i % 2 === 0 ? '#2B3BE5' : '#2BE58B',
        domain: 'void'
      }));
    }
    return [
      { id: 'general', position: [10, 2, 10], label: 'DOMAIN GATE', color: '#2B3BE5', domain: 'General' },
      { id: 'intelligence', position: [-10, 2, -10], label: 'ARCHI FORGE', color: '#E52B3B', domain: 'Forge' },
      { id: 'memory', position: [15, 2, -15], label: 'PERSISTENCE', color: '#2BE58B', domain: 'Persistence' },
      { id: 'strike', position: [-5, 2, 15], label: 'STRIKE CONSOLE', color: '#E5D12B', domain: 'Strike' },
    ];
  }, [isFrontierMode]);

  const groupRef = useRef<THREE.Group>(null);
  const prevFactCount = useRef(factCount);
  const jumpTime = useRef(0);

  // Ω-PERSIST: Calculate domain exergy intensity
  const getDomainState = (domainName: string) => {
    const domainFacts = hechosSoberanos.filter(f => f.dominio === domainName);
    if (domainFacts.length === 0) return { exergy: 0, crystallized: false };
    
    const maxExergy = Math.max(...domainFacts.map(f => f.exergia));
    const hasCrystallized = domainFacts.some(f => f.cristalizado === 1);
    return { exergy: maxExergy, crystallized: hasCrystallized };
  };

  useFrame((state) => {
    if (!groupRef.current) return;
    
    const time = state.clock.getElapsedTime();
    const entropyFactor = measuredEntropy / 100;

    // React to Fact commits
    if (factCount !== prevFactCount.current) {
      prevFactCount.current = factCount;
      jumpTime.current = time;
    }

    groupRef.current.children.forEach((child, i) => {
      const nodeDef = nodes[i];
      if (!nodeDef) return;

      if (isFrontierMode) {
        // Warp Animation: Streaks moving towards camera
        const speed = 0.5 + (measuredEntropy / 50);
        child.position.z += speed;
        if (child.position.z > 50) {
          child.position.z = -150;
        }
        child.scale.set(0.1, 0.1, 8); // Elongated streaks
        return;
      }

      const { exergy, crystallized } = getDomainState(nodeDef.domain);

      if (child instanceof THREE.Group) {
        // Floating animation modualted by exergy
        const floatFreq = 1 + exergy * 2;
        child.position.y = Math.sin(time * floatFreq + i) * (0.1 + exergy * 0.2);
        
        // React to Entropy + Exergy: Wobble
        child.rotation.y += (0.01 + entropyFactor * 0.05 + exergy * 0.02);
        
        // Exergy Pulse: Nodes pulse if they have facts
        if (exergy > 0 || crystallized) {
          const pulseScale = crystallized ? 1.05 : 1 + Math.sin(time * 3) * 0.05 * exergy;
          child.scale.lerp(new THREE.Vector3(pulseScale, pulseScale, pulseScale), 0.1);
        }

        // Commits / Jumps
        const jumpElapsed = time - jumpTime.current;
        if (jumpElapsed < 1) {
          const s = 1 + Math.sin(jumpElapsed * Math.PI * 5) * 0.15 * (1 - jumpElapsed);
          child.scale.set(s, s, s);
        }

        // Archi Loading (Special case)
        if (isArchiLoading && nodeDef.id === 'intelligence') {
          const s = 1.2 + Math.sin(time * 15) * 0.1;
          child.scale.set(s, s, s);
        }
      }
    });
  });

  return (
    <group ref={groupRef}>
      {nodes.map((node, i) => {
        const { exergy, crystallized } = getDomainState(node.domain);
        const intensity = crystallized ? 3.0 : 0.8 + (exergy * 1.5) + (measuredEntropy / 100);

        return (
          <group key={i} position={node.position as [number, number, number]}>
            <RigidBody type="fixed" colliders={false}>
              <mesh castShadow={!isFrontierMode} receiveShadow={!isFrontierMode}>
                <boxGeometry args={isFrontierMode ? [0.1, 0.1, 1] : [2, 4, 2]} />
                <meshStandardMaterial 
                  color={isFrontierMode ? node.color : "#000"} 
                  emissive={node.color} 
                  emissiveIntensity={isFrontierMode ? 10 : intensity * 0.5}
                  roughness={0}
                  metalness={1}
                  transparent={isFrontierMode}
                  opacity={isFrontierMode ? 0.8 : 1}
                />
              </mesh>
              
              <CuboidCollider 
                args={[3, 4, 3]} 
                sensor 
                onIntersectionEnter={() => {
                  setProximityNode(node.id);
                  sonic.playClick('proximity');
                }}
                onIntersectionExit={() => setProximityNode(null)}
              />

              {proximityNode === node.id && (
                <Html position={[0, 5, 0]} center distanceFactor={10}>
                  <div className="proximity-prompt-minimal">
                    <span className="node-id-tag">{node.label}</span>
                  </div>
                </Html>
              )}

              {/* Aura / Glow Layer */}
              <mesh position={[0, 0, 0]} scale={[1.1, 1.05, 1.1]}>
                <boxGeometry args={[2, 4, 2]} />
                <meshBasicMaterial 
                  color={node.color} 
                  transparent 
                  opacity={0.1 + (exergy * 0.3) + (measuredEntropy / 200)} 
                />
              </mesh>
            </RigidBody>
          </group>
        );
      })}
    </group>
  );
};

export default Nodes;
