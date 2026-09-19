import { Metric } from "@/components/Metric";
import { formatTelemetryValue } from "@/types";
import rocketImage from '@/assets/rocket.png';

function TelemetryPage({
    rotationAngle,
    time,
    altitude,
}: {
    rotationAngle: number;
    time: number | null;
    altitude: number | null;
}) {
    return (
        <div className="relative w-full min-h-screen flex items-center justify-center overflow-hidden">
            <div className="absolute top-12 z-10 flex justify-center w-full">
                <div className="grid grid-cols-2 gap-x-[25rem] px-4 sm:px-8 md:px-16">
                    <Metric large metrics={{ title: "Time", value: formatTelemetryValue(time), unit: "s" }} />
                    <Metric
                        large
                        metrics={{
                            title: "Altitude",
                            value: formatTelemetryValue(altitude),
                            unit: "ft",
                        }}
                    />
                </div>
            </div>

            
            <img
                className="relative z-0 w-[16vh] max-w-full h-auto"
                src={rocketImage}
                alt="Rocket"
                style={{ transform: `translateY(-5px) rotate(${rotationAngle}deg)` }}
            />
        </div>
    );
}

export default TelemetryPage;


