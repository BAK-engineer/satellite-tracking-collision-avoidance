import React, { useRef, useEffect, useState, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Stars, Text, Html, Line } from '@react-three/drei';
import * as THREE from 'three';
import { motion } from 'framer-motion';

// Types
interface Satellite {
  id: string;
  name: string;
  position: [number, number, number];
  velocity: [number, number, number];
  altitude: number;
  is_maneuvering: boolean;
  mission_type: string;
  color: string;
  norad_id: number;
}

interface OrbitalSceneProps {
  satellites: Satellite[];
  selectedSatellite: string | null;
  onSatelliteSelect: (id: string) => void;
  showOrbits: boolean;
  showDebris: boolean;
  timeSpeed: number;
  cameraTarget: 'earth' | 'satellite' | 'free';
}

// Earth Component
const Earth: React.FC<{ rotationSpeed: number }> = ({ rotationSpeed }) => {
  const earthRef = useRef<THREE.Mesh>(null);
  const atmosphereRef = useRef<THREE.Mesh>(null);
  
  useFrame((state, delta) => {
    if (earthRef.current) {
      earthRef.current.rotation.y += rotationSpeed * delta;
    }
    if (atmosphereRef.current) {
      atmosphereRef.current.rotation.y += rotationSpeed * delta * 0.5;
    }
  });

  const earthTexture = useMemo(() => {
    const loader = new THREE.TextureLoader();
    return loader.load('/textures/earth_daymap.jpg');
  }, []);

  const nightTexture = useMemo(() => {
    const loader = new THREE.TextureLoader();
    return loader.load('/textures/earth_nightmap.jpg');
  }, []);

  return (
    <group>
      {/* Earth */}
      <mesh ref={earthRef} position={[0, 0, 0]}>
        <sphereGeometry args={[6.371, 64, 64]} />
        <meshPhongMaterial
          map={earthTexture}
          emissiveMap={nightTexture}
          emissive={new THREE.Color(0x112244)}
          emissiveIntensity={0.1}
          shininess={100}
        />
      </mesh>
      
      {/* Atmosphere */}
      <mesh ref={atmosphereRef} position={[0, 0, 0]}>
        <sphereGeometry args={[6.5, 32, 32]} />
        <meshPhongMaterial
          color={0x87ceeb}
          transparent
          opacity={0.1}
          side={THREE.BackSide}
        />
      </mesh>
      
      {/* Clouds */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[6.38, 32, 32]} />
        <meshPhongMaterial
          color={0xffffff}
          transparent
          opacity={0.05}
        />
      </mesh>
    </group>
  );
};

// Satellite Component
const SatelliteObject: React.FC<{
  satellite: Satellite;
  isSelected: boolean;
  onClick: () => void;
  timeSpeed: number;
}> = ({ satellite, isSelected, onClick, timeSpeed }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const orbitRef = useRef<THREE.Group>(null);
  const [angle, setAngle] = useState(0);

  useFrame((state, delta) => {
    if (meshRef.current && orbitRef.current) {
      // Calculate orbital motion
      const radius = Math.sqrt(
        satellite.position[0] ** 2 + satellite.position[1] ** 2 + satellite.position[2] ** 2
      );
      
      const orbitalSpeed = Math.sqrt(398600.4418 / radius) * 0.001; // Simplified orbital mechanics
      const newAngle = angle + orbitalSpeed * delta * timeSpeed;
      setAngle(newAngle);
      
      // Update position
      const x = Math.cos(newAngle) * radius;
      const z = Math.sin(newAngle) * radius;
      const y = satellite.position[1]; // Keep inclination
      
      meshRef.current.position.set(x, y, z);
      
      // Rotation
      meshRef.current.rotation.x += delta * 2;
      meshRef.current.rotation.y += delta * 1;
      
      // Maneuvering effects
      if (satellite.is_maneuvering) {
        const pulse = Math.sin(state.clock.elapsedTime * 4) * 0.2 + 1;
        meshRef.current.scale.setScalar(pulse);
      }
    }
  });

  const color = new THREE.Color(satellite.color);
  const emissiveIntensity = satellite.is_maneuvering ? 0.5 : 0.2;

  return (
    <group ref={orbitRef}>
      <mesh
        ref={meshRef}
        position={satellite.position}
        onClick={onClick}
        onPointerOver={(e) => {
          e.stopPropagation();
          document.body.style.cursor = 'pointer';
        }}
        onPointerOut={() => {
          document.body.style.cursor = 'auto';
        }}
      >
        {/* Satellite body */}
        <boxGeometry args={[0.2, 0.2, 0.4]} />
        <meshPhongMaterial
          color={color}
          emissive={color}
          emissiveIntensity={emissiveIntensity}
        />
        
        {/* Solar panels */}
        <mesh position={[-0.3, 0, 0]}>
          <boxGeometry args={[0.4, 0.05, 0.3]} />
          <meshPhongMaterial color={0x1a1a2e} />
        </mesh>
        <mesh position={[0.3, 0, 0]}>
          <boxGeometry args={[0.4, 0.05, 0.3]} />
          <meshPhongMaterial color={0x1a1a2e} />
        </mesh>
        
        {/* Maneuvering thruster */}
        {satellite.is_maneuvering && (
          <mesh position={[0, 0, -0.3]}>
            <coneGeometry args={[0.05, 0.3, 8]} />
            <meshPhongMaterial
              color={0xffff00}
              emissive={0xffff00}
              emissiveIntensity={0.8}
            />
          </mesh>
        )}
        
        {/* Label */}
        <Html distanceFactor={10}>
          <div
            style={{
              background: isSelected ? 'rgba(255, 107, 107, 0.9)' : 'rgba(0, 255, 159, 0.9)',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 'bold',
              whiteSpace: 'nowrap',
              transform: 'translate(-50%, -100%)',
              marginBottom: '10px',
              border: isSelected ? '2px solid #ff6b6b' : '1px solid #00ff9f',
              boxShadow: '0 2px 10px rgba(0,0,0,0.5)',
            }}
          >
            {satellite.name}
            {satellite.is_maneuvering && <span style={{ marginLeft: '8px' }}>🚀</span>}
          </div>
        </Html>
      </mesh>
    </group>
  );
};

// Orbital Path Component
const OrbitalPath: React.FC<{ satellite: Satellite; color: string }> = ({ satellite, color }) => {
  const points = useMemo(() => {
    const radius = Math.sqrt(
      satellite.position[0] ** 2 + satellite.position[1] ** 2 + satellite.position[2] ** 2
    );
    
    const orbitPoints: THREE.Vector3[] = [];
    for (let i = 0; i <= 64; i++) {
      const angle = (i / 64) * Math.PI * 2;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const y = satellite.position[1]; // Simplified inclination
      orbitPoints.push(new THREE.Vector3(x, y, z));
    }
    return orbitPoints;
  }, [satellite]);

  return (
    <Line
      points={points}
      color={color}
      lineWidth={1}
      transparent
      opacity={0.3}
    />
  );
};

// Debris Field Component
const DebrisField: React.FC = () => {
  const debrisRef = useRef<THREE.InstancedMesh>(null);
  const count = 1000;

  useEffect(() => {
    if (debrisRef.current) {
      const dummy = new THREE.Object3D();
      
      for (let i = 0; i < count; i++) {
        // Random orbital positions
        const radius = 7 + Math.random() * 15; // 400-2000km altitude
        const angle = Math.random() * Math.PI * 2;
        const inclination = (Math.random() - 0.5) * Math.PI * 0.5;
        
        dummy.position.set(
          Math.cos(angle) * radius * Math.cos(inclination),
          Math.sin(inclination) * radius,
          Math.sin(angle) * radius * Math.cos(inclination)
        );
        
        dummy.scale.setScalar(Math.random() * 0.02 + 0.01);
        dummy.updateMatrix();
        debrisRef.current.setMatrixAt(i, dummy.matrix);
      }
      debrisRef.current.instanceMatrix.needsUpdate = true;
    }
  }, []);

  useFrame((state, delta) => {
    if (debrisRef.current) {
      debrisRef.current.rotation.y += delta * 0.1;
    }
  });

  return (
    <instancedMesh ref={debrisRef} args={[undefined, undefined, count]}>
      <sphereGeometry args={[1, 6, 6]} />
      <meshBasicMaterial color={0x808080} transparent opacity={0.6} />
    </instancedMesh>
  );
};

// Camera Controller
const CameraController: React.FC<{
  target: 'earth' | 'satellite' | 'free';
  selectedSatellite: Satellite | null;
}> = ({ target, selectedSatellite }) => {
  const { camera } = useThree();
  
  useFrame(() => {
    if (target === 'earth') {
      camera.position.lerp(new THREE.Vector3(0, 5, 15), 0.02);
      camera.lookAt(0, 0, 0);
    } else if (target === 'satellite' && selectedSatellite) {
      const satPos = new THREE.Vector3(...selectedSatellite.position);
      const targetPos = satPos.clone().add(new THREE.Vector3(2, 2, 2));
      camera.position.lerp(targetPos, 0.02);
      camera.lookAt(satPos);
    }
  });

  return null;
};

// Main Scene Component
const Scene: React.FC<OrbitalSceneProps> = ({
  satellites,
  selectedSatellite,
  onSatelliteSelect,
  showOrbits,
  showDebris,
  timeSpeed,
  cameraTarget,
}) => {
  const selectedSat = satellites.find(s => s.id === selectedSatellite) || null;

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.3} />
      <directionalLight
        position={[100, 50, 50]}
        intensity={1.5}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      <pointLight position={[0, 0, 0]} intensity={0.5} color={0xffff88} />

      {/* Environment */}
      <Stars radius={300} depth={60} count={3000} factor={7} saturation={0} fade />
      
      {/* Earth */}
      <Earth rotationSpeed={timeSpeed * 0.1} />
      
      {/* Satellites */}
      {satellites.map((satellite) => (
        <React.Fragment key={satellite.id}>
          <SatelliteObject
            satellite={satellite}
            isSelected={selectedSatellite === satellite.id}
            onClick={() => onSatelliteSelect(satellite.id)}
            timeSpeed={timeSpeed}
          />
          {showOrbits && (
            <OrbitalPath
              satellite={satellite}
              color={satellite.color}
            />
          )}
        </React.Fragment>
      ))}
      
      {/* Debris */}
      {showDebris && <DebrisField />}
      
      {/* Camera Controller */}
      <CameraController target={cameraTarget} selectedSatellite={selectedSat} />
      
      {/* Controls */}
      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={8}
        maxDistance={100}
        autoRotate={cameraTarget === 'free'}
        autoRotateSpeed={0.5}
      />
    </>
  );
};

// Main Component
const OrbitalScene: React.FC<OrbitalSceneProps> = (props) => {
  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Canvas
        camera={{ position: [0, 5, 15], fov: 60 }}
        style={{ background: 'radial-gradient(ellipse at center, #001122 0%, #000000 100%)' }}
        gl={{ antialias: true, alpha: false }}
        shadows
      >
        <Scene {...props} />
      </Canvas>
      
      {/* Performance overlay */}
      <div
        style={{
          position: 'absolute',
          top: 10,
          left: 10,
          color: '#00ff9f',
          fontSize: '12px',
          fontFamily: 'monospace',
          background: 'rgba(0, 0, 0, 0.7)',
          padding: '8px',
          borderRadius: '4px',
        }}
      >
        <div>🌍 3D Orbital Visualization</div>
        <div>📡 Satellites: {props.satellites.length}</div>
        <div>⚡ Time Speed: {props.timeSpeed}x</div>
        <div>🚀 Maneuvering: {props.satellites.filter(s => s.is_maneuvering).length}</div>
      </div>
    </div>
  );
};

export default OrbitalScene;