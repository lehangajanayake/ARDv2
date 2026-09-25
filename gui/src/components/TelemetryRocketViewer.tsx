import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { ModelErrorBoundary, RocketData, RocketModel } from "./RocketModel";

function TelemetryRocketViewer({ data }: { data: RocketData }) {
	const preview = data.gyroX === null && data.gyroY === null && data.gyroZ === null;

	return (
		<div className="aspect-[2/3] w-full">
			<ModelErrorBoundary>
				<Canvas camera={{ position: [0, 0, 7], fov: 42 }}>
					<ambientLight intensity={1.5} />
					<directionalLight position={[3, 4, 5]} intensity={2} />
					<Suspense fallback={null}>
						<RocketModel data={data} modelScale={2} preview={preview} />
					</Suspense>
				</Canvas>
			</ModelErrorBoundary>
		</div>
	);
}

export default TelemetryRocketViewer;