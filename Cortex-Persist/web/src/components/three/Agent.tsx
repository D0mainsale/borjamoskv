import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useKeyboardControls, Html } from '@react-three/drei';
import { RigidBody, RapierRigidBody, vec3 } from '@react-three/rapier';
import * as THREE from 'three';
import './Agent.css';

interface AgentProps {
  exergyLevel: number;
}

const Agent: React.FC<AgentProps> = ({ exergyLevel }) => {
  const body = useRef<RapierRigidBody>(null);
  const [, getKeys] = useKeyboardControls();
  const chassisRef = useRef<THREE.Mesh>(null);
  const hudRef = useRef<HTMLDivElement>(null);

  useFrame((state, delta) => {
    if (!body.current) return;

    const { forward, backward, left, right, jump, boost } = getKeys();
    
    // Movement Logic
    const impulse = { x: 0, y: 0, z: 0 };
    const torque = { x: 0, y: 0, z: 0 };
    
    const impulseStrength = (boost ? 40 : 20) * delta;
    const torqueStrength = 15 * delta;

    if (forward) impulse.z -= impulseStrength;
    if (backward) impulse.z += impulseStrength;
    if (left) torque.y += torqueStrength;
    if (right) torque.y -= torqueStrength;

    // Apply movement
    const rotation = body.current.rotation();
    const rotatedImpulse = new THREE.Vector3(impulse.x, impulse.y, impulse.z).applyQuaternion(
      new THREE.Quaternion(rotation.x, rotation.y, rotation.z, rotation.w)
    );
    
    body.current.applyImpulse(rotatedImpulse, true);
    body.current.applyTorqueImpulse(torque, true);

    if (jump && Math.abs(body.current.linvel().y) < 0.1) {
      body.current.applyImpulse({ x: 0, y: 5, z: 0 }, true);
    }

    // Camera follow (Lerp)
    const bodyPos = vec3(body.current.translation());
    const cameraOffset = new THREE.Vector3(0, 5, 12).applyQuaternion(
      new THREE.Quaternion(rotation.x, rotation.y, rotation.z, rotation.w)
    );
    const targetCameraPos = bodyPos.clone().add(cameraOffset);
    
    state.camera.position.lerp(targetCameraPos, 0.1);
    state.camera.lookAt(bodyPos);

    // Visual Reactivity: Engine Glow
    if (chassisRef.current) {
      const mat = chassisRef.current.material as THREE.MeshStandardMaterial;
      mat.emissiveIntensity = 0.5 + (exergyLevel / 100) * 1.5 + (boost ? 1.0 : 0);
    }
    
    if (hudRef.current) {
      hudRef.current.style.setProperty('--progress-width', `${exergyLevel}%`);
    }
  });

  return (
    <group>
      <RigidBody
        ref={body}
        colliders="hull"
        position={[0, 5, 0]}
        enabledRotations={[false, true, false]}
        linearDamping={0.5}
        angularDamping={0.5}
      >
        {/* Chassis */}
        <mesh ref={chassisRef} castShadow>
          <boxGeometry args={[1, 0.5, 2]} />
          <meshStandardMaterial 
            color="#0A0A0A" 
            emissive="#2B3BE5" 
            emissiveIntensity={1} 
            metalness={1} 
            roughness={0} 
          />
          
          {/* Tactical Proximity HUD */}
          <Html position={[0, 1.5, 0]} center distanceFactor={10}>
            <div ref={hudRef} className="agent-proximity-hud">
              <div className="hud-line">
                <span className="label">EXE:</span>
                <span className="value">{(exergyLevel).toFixed(1)}%</span>
              </div>
              <div className="hud-progress-container">
                <div className="hud-progress-bar"></div>
              </div>
            </div>
          </Html>
        </mesh>
        
        {/* Wheels / Thrusters */}
        <mesh position={[0.6, -0.2, 0.7]}>
          <boxGeometry args={[0.2, 0.4, 0.4]} />
          <meshStandardMaterial color="#222" />
        </mesh>
        <mesh position={[-0.6, -0.2, 0.7]}>
          <boxGeometry args={[0.2, 0.4, 0.4]} />
          <meshStandardMaterial color="#222" />
        </mesh>
        <mesh position={[0.6, -0.2, -0.7]}>
          <boxGeometry args={[0.2, 0.4, 0.4]} />
          <meshStandardMaterial color="#222" />
        </mesh>
        <mesh position={[-0.6, -0.2, -0.7]}>
          <boxGeometry args={[0.2, 0.4, 0.4]} />
          <meshStandardMaterial color="#222" />
        </mesh>
      </RigidBody>
    </group>
  );
};

export default Agent;
