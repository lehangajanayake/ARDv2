import { useEffect, useState } from "react";
import { Telemetry } from "../types";

interface Props {
	data: Pick<Telemetry, "gyroX" | "gyroY" | "gyroZ">;
}

const axisColors = {
	x: "#ff668f",
	y: "#65f7bf",
	z: "#5ad8ff",
};

type Vector3 = { x: number; y: number; z: number };

function rotateVector(vector: Vector3, roll: number, pitch: number, yaw: number) {
	const rollCos = Math.cos(roll);
	const rollSin = Math.sin(roll);
	const pitchCos = Math.cos(pitch);
	const pitchSin = Math.sin(pitch);
	const yawCos = Math.cos(yaw);
	const yawSin = Math.sin(yaw);

	const rolled = {
		x: vector.x,
		y: vector.y * rollCos - vector.z * rollSin,
		z: vector.y * rollSin + vector.z * rollCos,
	};
	const pitched = {
		x: rolled.x * pitchCos + rolled.z * pitchSin,
		y: rolled.y,
		z: -rolled.x * pitchSin + rolled.z * pitchCos,
	};

	return {
		x: pitched.x * yawCos - pitched.y * yawSin,
		y: pitched.x * yawSin + pitched.y * yawCos,
		z: pitched.z,
	};
}

function projectVector(vector: Vector3, center: number, length: number) {
	return {
		x: center + (vector.x - vector.y * 0.45) * length,
		y: center + (-vector.z + vector.y * 0.25) * length,
	};
}

function Gyro({ data }: Props) {
	const [mockTime, setMockTime] = useState(0);

	useEffect(() => {
		const timer = window.setInterval(() => setMockTime((time) => time + 0.08), 80);
		return () => window.clearInterval(timer);
	}, []);

	const mockData = {
		gyroX: Math.sin(mockTime) * 45,
		gyroY: Math.cos(mockTime * 0.8) * 45,
		gyroZ: Math.sin(mockTime * 0.55 + 1) * 45,
	};
	const toAngle = (value: number) => Math.tanh(value / 90) * Math.PI;
	const roll = toAngle(data.gyroX ?? mockData.gyroX);
	const pitch = toAngle(data.gyroY ?? mockData.gyroY);
	const yaw = toAngle(data.gyroZ ?? mockData.gyroZ);
	const center = 110;
	const lineLength = 68;
	const axes = [
		{ vector: rotateVector({ x: 1, y: 0, z: 0 }, roll, pitch, yaw), color: axisColors.x },
		{ vector: rotateVector({ x: 0, y: 1, z: 0 }, roll, pitch, yaw), color: axisColors.y },
		{ vector: rotateVector({ x: 0, y: 0, z: 1 }, roll, pitch, yaw), color: axisColors.z },
	].map(({ vector, color }) => {
		const endpoint = projectVector(vector, center, lineLength);
		return { endpoint, color };
	});

	return (
		<div className="flex flex-col items-center w-full h-full">
			<h2 className="text-center text-gray-300 text-sm sm:text-base">
				Rocket Gyro Axes
			</h2>
			<div className="h-48">
			<svg className="h-full w-full" viewBox="0 0 220 220">
				<defs>
					<marker id="gyro-arrow-x" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto">
						<path d="M0,0 L7,3.5 L0,7 Z" fill={axisColors.x} />
					</marker>
					<marker id="gyro-arrow-y" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto">
						<path d="M0,0 L7,3.5 L0,7 Z" fill={axisColors.y} />
					</marker>
					<marker id="gyro-arrow-z" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto">
						<path d="M0,0 L7,3.5 L0,7 Z" fill={axisColors.z} />
					</marker>
				</defs>
				{axes.map(({ endpoint, color }) => (
					<line
						key={color}
						x1={center}
						y1={center}
						x2={endpoint.x}
						y2={endpoint.y}
						stroke={color}
						strokeWidth="3"
						strokeLinecap="round"
						markerEnd={`url(#gyro-arrow-${color === axisColors.x ? "x" : color === axisColors.y ? "y" : "z"})`}
					/>
				))}
			</svg>
			</div>
		</div>
	);
}

export default Gyro;
