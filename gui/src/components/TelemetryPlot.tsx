import { Telemetry } from "@/types";
import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";

export type ChartData = Record<string, number>;

interface TelemetryPlotProps {
  data: Telemetry[];
  title: string;
  dataKey: keyof Telemetry;
  color?: string;
  referenceValue?: number;
  referenceLabel?: string;
  referenceColor?: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  yAxisUnit?: string;
}

export const TelemetryPlot: React.FC<TelemetryPlotProps> = ({
  data,
  title,
  dataKey,
  color = "yellow",
  referenceValue,
  referenceLabel,
  referenceColor = "#60a5fa",
  xAxisLabel = "Time (s)",
  yAxisLabel,
  yAxisUnit,
}) => {
  return (
    <div className="flex flex-col items-center w-full h-full">
      <h2 className="text-center text-gray-300 text-sm sm:text-base">{title}</h2>
      <div className="w-full h-40 sm:h-48 md:h-56">
        <ResponsiveContainer width="100%" height="80%">
          <LineChart data={data} margin={{ bottom: 16, left: 8 }}>
            <XAxis
              dataKey="time"
              tick={{ fill: "white", fontSize: 10 }}
              domain={['auto', 'auto']}
              label={{
                value: xAxisLabel,
                position: "insideBottom",
                offset: -8,
                fill: "#9ca3af",
                fontSize: 10,
              }}
            />
            <YAxis
              tick={{ fill: "white", fontSize: 10 }}
              domain={['auto', 'auto']}
              tickFormatter={
                yAxisUnit ? (value: number) => `${value} ${yAxisUnit}` : undefined
              }
              label={
                yAxisLabel
                  ? {
                      value: yAxisLabel,
                      angle: -90,
                      position: "insideLeft",
                      fill: "#9ca3af",
                      fontSize: 10,
                    }
                  : undefined
              }
            />
            <Tooltip
              contentStyle={{ backgroundColor: "black", borderColor: "white" }}
              itemStyle={{ color: "white" }}
            />
            {referenceValue !== undefined && (
              <ReferenceLine
                y={referenceValue}
                stroke={referenceColor}
                strokeDasharray="4 4"
                label={
                  referenceLabel
                    ? { value: referenceLabel, fill: referenceColor, fontSize: 10, position: "insideTopRight" }
                    : undefined
                }
              />
            )}
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

