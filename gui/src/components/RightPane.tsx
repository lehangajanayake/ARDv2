
import { formatTelemetryValue, Telemetry } from "../types";
import { TelemetryPlot } from "./TelemetryPlot";

const calculatePercentage = (value: number | null, max: number) =>
  value === null ? 0 : (Math.min(Math.max(value, 0), max) / max) * 100;

interface Props {
  data: Telemetry;
  history: Telemetry[];
  targetHeight: number;
}

const RightPane = ({ data, history, targetHeight }: Props) => {
  const accelerationMetrics = [
    { title: "Acceleration X", value: data.accX, unit: "m/s²", max: 10 },
    { title: "Acceleration Y", value: data.accY, unit: "m/s²", max: 10 },
    { title: "Acceleration Z", value: data.accZ, unit: "m/s²", max: 10 },
  ];

  return (
    <div className="w-full max-w-xs space-y-14">
      <div className="space-y-8">
        {accelerationMetrics.map((item, index) => (
          <div key={index} className="flex justify-between items-end">
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
            <div className="pl-6 text-lg text-white whitespace-nowrap">
              {formatTelemetryValue(item.value)} {item.unit}
            </div>
          </div>
        ))}
      </div>

      <TelemetryPlot
        data={history}
        title="Live Height"
        dataKey="altitude"
        color="#ffbd2e"
        referenceValue={targetHeight}
        referenceLabel="Target"
        xAxisLabel="Time (s)"
        yAxisLabel="Altitude (ft)"
        yAxisUnit="ft"
      />
    </div>
  );
};

export default RightPane;
