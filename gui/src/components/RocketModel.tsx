import { Component, type ReactNode } from "react";
import { useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { Box3, Group, Vector3 } from "three";
import { useMemo, useRef } from "react";
import { Telemetry } from "../types";

const modelPath = "/models/rocket.glb";

export type RocketData = Pick<Telemetry, "gyroX" | "gyroY" | "gyroZ">;

export function RocketModel({
	data,
	modelScale,
	preview = false,
}: {
	data: RocketData;
	modelScale: number;
	preview?: boolean;
}) {
	const { scene } = useGLTF(modelPath);
	const toAngle = (value: number | null) => Math.tanh((value ?? 0) / 90) * Math.PI;
	const modelCenter = useMemo(() => {
		const model = scene.clone(true);
		model.position.set(0, 0, 0);
		model.rotation.set(0, 0, 0);
		model.scale.set(1, 1, 1);
		model.updateMatrixWorld(true);
		return new Box3().setFromObject(model).getCenter(new Vector3());
	}, [scene]);
	const rotationGroup = useRef<Group>(null);

	useFrame((state) => {
		if (!preview || !rotationGroup.current) return;
		const time = state.clock.elapsedTime;
		rotationGroup.current.rotation.set(
			Math.sin(time * 0.7) * 0.25,
			time * 0.45,
			Math.sin(time * 0.5) * 0.18,
		);
	});

	return (
		<group
			ref={rotationGroup}
			rotation={preview ? [0, 0, 0] : [toAngle(data.gyroY), toAngle(data.gyroZ), toAngle(data.gyroX)]}
		>
			<group position={[-modelCenter.x * modelScale, -modelCenter.y * modelScale, -modelCenter.z * modelScale]}>
				<primitive object={scene} scale={modelScale} />
			</group>
		</group>
	);
}

export class ModelErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
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