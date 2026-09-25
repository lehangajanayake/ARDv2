import { Metric } from "@/components/Metric";
import TelemetryRocketViewer from "@/components/TelemetryRocketViewer";
import { formatTelemetryValue } from "@/types";

function TelemetryPage({
    time,
    altitude,
    gyroX,
    gyroY,
    gyroZ,
}: {
    time: number | null;
    altitude: number | null;
    gyroX: number | null;
    gyroY: number | null;
    gyroZ: number | null;
}) {
    return (
        <div className="relative h-full min-h-0 w-full flex items-center justify-center overflow-hidden">
            <div className="absolute top-12 z-10 flex justify-center w-full">
                <div className="grid grid-cols-2 gap-x-[25rem] px-4 sm:px-8 md:px-16">
                    <Metric metrics={{ title: "Time", value: formatTelemetryValue(time), unit: "s" }} />
                    <Metric
                        metrics={{
                            title: "Altitude",
                            value: formatTelemetryValue(altitude),
                            unit: "ft",
                        }}
                    />
                </div>
            </div>

            
            <div className="absolute left-1/2 top-[clamp(8rem,20vh,14rem)] z-0 w-[min(62vw,30rem)] -translate-x-1/2">
                <TelemetryRocketViewer data={{ gyroX, gyroY, gyroZ }} />
            </div>
        </div>
    );
}

export default TelemetryPage;


