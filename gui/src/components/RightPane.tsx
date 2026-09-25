
import { formatTelemetryValue, Telemetry } from "../types";
import { TelemetryPlot } from "./TelemetryPlot";
import Gyro from "./Gyro";

const calculatePercentage = (value: number | null, max: number) =>
  value === null ? 0 : (Math.min(Math.max(value, 0), max) / max) * 100;

interface Props {
  data: Telemetry;
  history: Telemetry[];
  targetHeight: number;
  showGyro: boolean;
}

const RightPane = ({ data, history, targetHeight, showGyro }: Props) => {
  const accelerationMetrics = [
    { title: "Acceleration X", value: data.accX, unit: "m/s²", max: 10 },
    { title: "Acceleration Y", value: data.accY, unit: "m/s²", max: 10 },
    { title: "Acceleration Z", value: data.accZ, unit: "m/s²", max: 10 },
  ];

  return (
    <div className="flex h-full min-h-0 w-full max-w-xs flex-col items-center gap-10">
      <div className="w-full space-y-6">
        {accelerationMetrics.map((item, index) => (
          <div key={index} className="flex w-full items-end justify-center gap-5">
            <div className="flex flex-col space-y-2">
              <span className="text-md text-gray-300">{item.title}</span>
              <div className="relative w-36 h-1.5">
                <div className="w-36 absolute left-0 top-0 rounded-full h-1.5 bg-gray-600/20"></div>
                <div
                  className="absolute left-0 top-0 bg-blue rounded-full h-1.5"
                  style={{ width: `${calculatePercentage(item.value, item.max)}%` }}
                ></div>
              </div>
            </div>
            <div className="text-lg text-white whitespace-nowrap">
              {formatTelemetryValue(item.value)} {item.unit}
            </div>
          </div>
        ))}
      </div>
        
      <div className="w-full shrink-0">
        <TelemetryPlot
          data={history}
          title="Altitude"
          dataKey="altitude"
          color="#ffbd2e"
          referenceValue={targetHeight}
          referenceLabel="Target"
          xAxisLabel="Time (s)"
          yAxisLabel="Altitude (ft)"
          yAxisUnit="ft"
        />
      </div>

      {showGyro && (
        <div className="w-full shrink-0">
          <Gyro data={data} />
        </div>
      )}

    </div>
  );
};

export default RightPane;
