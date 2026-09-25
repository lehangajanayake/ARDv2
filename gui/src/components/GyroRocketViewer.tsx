import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { ModelErrorBoundary, RocketData, RocketModel } from "./RocketModel";

function GyroRocketViewer({ data }: { data: RocketData }) {
	return (
		<div className="aspect-[3/4] w-full">
			<ModelErrorBoundary>
				<Canvas camera={{ position: [0, 0, 7], fov: 42 }}>
					<ambientLight intensity={1.5} />
					<directionalLight position={[3, 4, 5]} intensity={2} />
					<Suspense fallback={null}>
						<RocketModel data={data} modelScale={1} />
					</Suspense>
					<OrbitControls enablePan={false} enableZoom={false} />
				</Canvas>
			</ModelErrorBoundary>
		</div>
	);
}

export default GyroRocketViewer;