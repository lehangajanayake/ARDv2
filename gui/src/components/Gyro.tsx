import { Telemetry } from "../types";
import GyroRocketViewer from "./GyroRocketViewer";

interface Props {
	data: Pick<Telemetry, "gyroX" | "gyroY" | "gyroZ">;
}

function Gyro({ data }: Props) {
	return (
		<div className="flex w-full flex-col items-center">
			<h2 className="text-center text-gray-300 text-sm sm:text-base">
				Rocket Gyro Axes
			</h2>
			<GyroRocketViewer data={data} />
		</div>
	);
}

export default Gyro;
