import { Component, Suspense, useEffect, useState, type ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import { Center, OrbitControls, useGLTF } from "@react-three/drei";
import { Telemetry } from "../types";

interface Props {
	data: Pick<Telemetry, "gyroX" | "gyroY" | "gyroZ">;
}

const modelPath = "/models/rocket.glb";

function RocketModel({ roll, pitch, yaw }: { roll: number; pitch: number; yaw: number }) {
	const { scene } = useGLTF(modelPath);

	return (
		<group rotation={[pitch, yaw, roll]}>
			<Center>
				<primitive object={scene} scale={1} />
			</Center>
		</group>
	);
}

class ModelErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
	state = { hasError: false };

	static getDerivedStateFromError() {
		return { hasError: true };
	}

	render() {
		if (this.state.hasError) {
			return <p className="px-4 text-center text-xs text-gray-500">Add rocket.glb to public/models.</p>;
		}

		return this.props.children;
	}
}

function Gyro({ data }: Props) {
	const [mockTime, setMockTime] = useState(0);

	useEffect(() => {
		const timer = window.setInterval(() => setMockTime((time) => time + 0.08), 80);
		return () => window.clearInterval(timer);
	}, []);

	// const mockData = {
	// 	gyroX: Math.sin(mockTime) * 45,
	// 	gyroY: Math.cos(mockTime * 0.8) * 45,
	// 	gyroZ: Math.sin(mockTime * 0.55 + 1) * 45,
	// };
	const toAngle = (value: number) => Math.tanh(value / 90) * Math.PI;
	const roll = toAngle(data.gyroX ?? 0); // replace with mockData.gyroX if needed
	const pitch = toAngle(data.gyroY ?? 0); // replace with mockData.gyroY if needed
	const yaw = toAngle(data.gyroZ ?? 0); // replace with mockData.gyroZ if needed
	return (
		<div className="flex flex-col items-center w-full h-full">
			<h2 className="text-center text-gray-300 text-sm sm:text-base">
				Rocket Gyro Axes
			</h2>
			<div className="h-48 w-full">
				<ModelErrorBoundary>
					<Canvas camera={{ position: [0, 0, 4], fov: 42 }}>
						<ambientLight intensity={1.5} />
						<directionalLight position={[3, 4, 5]} intensity={2} />
						<Suspense fallback={null}>
							<RocketModel roll={roll} pitch={pitch} yaw={yaw} />
						</Suspense>
						<OrbitControls enablePan={false} enableZoom={false} />
					</Canvas>
				</ModelErrorBoundary>
			</div>
		</div>
	);
}

export default Gyro;
