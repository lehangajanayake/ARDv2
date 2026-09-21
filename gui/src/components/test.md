Certainly! I'll help you refactor your `Details` and `TelemetryPlot` components to improve their responsiveness and adjust the sizing for better display on smaller screens.

---

## Overview

We'll focus on the following:

1. **Details Component:**
   - Adjust the grid layout for plots to be responsive.
   - Make the table horizontally scrollable on smaller screens.
   - Adjust paddings and margins for better spacing.

2. **TelemetryPlot Component:**
   - Ensure the charts resize correctly using `ResponsiveContainer`.
   - Adjust text sizes and container sizes for different screen sizes.

---

## 1. Refactoring the **Details** Component

### Changes:

- **Grid Layout for Telemetry Plots:**
  - Use Tailwind CSS responsive classes to adjust the number of columns based on screen size.
  - On small screens, display one plot per row. Increase the number of columns on larger screens.

- **Table:**
  - Make the table container horizontally scrollable on smaller screens to handle overflow.
  - Adjust the max height and overflow properties for better vertical scrolling.

- **Spacing and Padding:**
  - Adjust paddings and margins using responsive utilities.

### Updated `Details.jsx` Component:

```jsx
import { PLOT_METADATA, TelemetryData } from "@/types";
import { TelemetryPlot } from "./TelemetryPlot";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

interface Props {
  data: TelemetryData[];
}

const Details = ({ data }: Props) => {
  return (
    <div className="pt-4 px-4 sm:px-6 md:px-8">
      <div className="pb-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {PLOT_METADATA.map((item) => (
            <TelemetryPlot
              key={item.key}
              data={data}
              title={item.label}
              dataKey={item.key}
              color={item.color}
            />
          ))}
        </div>
      </div>

      <h2 className="text-xl font-bold text-white mb-4">Latest Data</h2>

      <div className="overflow-x-auto">
        <div className="min-w-full inline-block align-middle">
          <div className="overflow-hidden shadow-md rounded-lg">
            <Table className="min-w-full bg-none">
              <TableHeader className="bg-gray-800">
                <TableRow>
                  <TableHead className="text-white">Time</TableHead>
                  <TableHead className="text-white">BMP Temp</TableHead>
                  <TableHead className="text-white">IMU Temp</TableHead>
                  <TableHead className="text-white">Pressure</TableHead>
                  <TableHead className="text-white">Altitude</TableHead>
                  <TableHead className="text-white">Acc X</TableHead>
                  <TableHead className="text-white">Acc Y</TableHead>
                  <TableHead className="text-white">Acc Z</TableHead>
                  <TableHead className="text-white">AngVel X</TableHead>
                  <TableHead className="text-white">AngVel Y</TableHead>
                  <TableHead className="text-white">AngVel Z</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className="bg-gray-700">
                {data.map((item, index) => (
                  <TableRow key={index}>
                    <TableCell className="text-white">{item.time}</TableCell>
                    <TableCell className="text-white">{item.bmpTemp}</TableCell>
                    <TableCell className="text-white">{item.imuTemp}</TableCell>
                    <TableCell className="text-white">{item.pressure}</TableCell>
                    <TableCell className="text-white">{item.altitude}</TableCell>
                    <TableCell className="text-white">{item.accX}</TableCell>
                    <TableCell className="text-white">{item.accY}</TableCell>
                    <TableCell className="text-white">{item.accZ}</TableCell>
                    <TableCell className="text-white">{item.gyroX}</TableCell>
                    <TableCell className="text-white">{item.gyroY}</TableCell>
                    <TableCell className="text-white">{item.gyroZ}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Details;
```

### Explanation:

1. **Grid Layout for Plots:**

   ```jsx
   <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
     {/* TelemetryPlot components */}
   </div>
   ```

   - **`grid-cols-1`**: On extra-small screens, display one plot per row.
   - **`sm:grid-cols-2`**: On small screens and up, display two plots per row.
   - **`lg:grid-cols-3`**: On large screens and up, display three plots per row.
   - **`gap-4`**: Adds consistent spacing between the plots.

2. **Table Responsiveness:**

   ```jsx
   <div className="overflow-x-auto">
     <div className="min-w-full inline-block align-middle">
       <div className="overflow-hidden shadow-md rounded-lg">
         <Table className="min-w-full bg-none">
           {/* Table content */}
         </Table>
       </div>
     </div>
   </div>
   ```

   - **`overflow-x-auto`**: Allows horizontal scrolling if the content overflows.
   - **`shadow-md` and `rounded-lg`**: Adds a subtle shadow and rounded corners for better aesthetics.
   - **Use of `min-w-full`**: Ensures the table takes up the full available width.

3. **Table Styling:**

   - Added **background colors** to the table header and body to differentiate them and improve readability.
   - Set **text color** to white for better contrast against the darker backgrounds.

4. **Spacing and Padding:**

   - **`pt-4 px-4 sm:px-6 md:px-8`**: Adds top padding and responsive horizontal padding.
     - **`px-4`**: Default horizontal padding.
     - **`sm:px-6`** and **`md:px-8`**: Increased padding on small and medium screens.

5. **Section Title:**

   ```jsx
   <h2 className="text-xl font-bold text-white mb-4">Latest Data</h2>
   ```

   - Increases the font size and adds margin below the heading for better separation from the content.

---

## 2. Refactoring the **TelemetryPlot** Component

### Changes:

- Ensure the chart container adjusts its width and height based on screen size.
- Adjust font sizes and spacing for better readability.

### Updated `TelemetryPlot.jsx` Component:

```jsx
import { TelemetryData } from "@/types";
import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export type ChartData = Record<string, number>;

interface TelemetryPlotProps {
  data: TelemetryData[];
  title: string;
  dataKey: keyof TelemetryData;
  color?: string;
}

export const TelemetryPlot: React.FC<TelemetryPlotProps> = ({
  data,
  title,
  dataKey,
  color = "yellow",
}) => {
  return (
    <div className="flex flex-col items-center w-full h-full">
      <h2 className="text-center text-gray-300 text-sm sm:text-base mb-2">{title}</h2>
      <div className="w-full h-40 sm:h-48 md:h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis
              dataKey="time"
              tick={{ fill: "white", fontSize: 10 }}
              domain={['auto', 'auto']}
            />
            <YAxis
              tick={{ fill: "white", fontSize: 10 }}
              domain={['auto', 'auto']}
            />
            <Tooltip
              contentStyle={{ backgroundColor: "black", borderColor: "white" }}
              itemStyle={{ color: "white" }}
            />
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
```

### Explanation:

1. **Container Adjustments:**

   ```jsx
   <div className="flex flex-col items-center w-full h-full">
     {/* Content */}
   </div>
   ```

   - **`w-full h-full`**: Ensures the component fills the available space.

2. **Title Styling:**

   ```jsx
   <h2 className="text-center text-gray-300 text-sm sm:text-base mb-2">{title}</h2>
   ```

   - **`text-sm`**: Smaller font size on extra-small screens.
   - **`sm:text-base`**: Base font size on small screens and up.
   - **`mb-2`**: Adds margin below the title for spacing.

3. **Chart Container:**

   ```jsx
   <div className="w-full h-40 sm:h-48 md:h-56">
     <ResponsiveContainer width="100%" height="100%">
       {/* LineChart */}
     </ResponsiveContainer>
   </div>
   ```

   - **Responsive Heights:**
     - **`h-40`**: 10rem height on extra-small screens.
     - **`sm:h-48`**: 12rem height on small screens.
     - **`md:h-56`**: 14rem height on medium screens and up.
   - These adjustments ensure the charts are visible and proportionate on different screen sizes.

4. **Axis Tick Styling:**

   ```jsx
   <XAxis
     dataKey="time"
     tick={{ fill: "white", fontSize: 10 }}
     domain={['auto', 'auto']}
   />
   <YAxis
     tick={{ fill: "white", fontSize: 10 }}
     domain={['auto', 'auto']}
   />
   ```

   - Adjusted **`fontSize: 10`** for better readability on smaller screens.

5. **ResponsiveContainer Settings:**

   ```jsx
   <ResponsiveContainer width="100%" height="100%">
     {/* LineChart */}
   </ResponsiveContainer>
   ```

   - Setting both width and height to `"100%"` ensures the chart scales to fit its parent container, which we've controlled via Tailwind CSS classes.

---

## 3. Additional Tips

- **Testing Responsiveness:**

  Make sure to test these components on different screen sizes. You can use your browser's developer tools to emulate various devices.

- **Consistent Styling:**

  Ensure that any custom components like `Table`, `TableRow`, etc., support className props so you can pass Tailwind CSS classes for consistent styling.

- **Using `className` Props:**

  If components like `TableCell` or `TableRow` do not accept a `className` prop, you may need to modify those components to accept it, allowing for more flexible styling.

  ```jsx
  // Example TableCell component modification
  const TableCell = ({ children, className }) => (
    <td className={`px-4 py-2 ${className}`}>{children}</td>
  );
  ```

---

## Conclusion

By implementing these changes, your `Details` and `TelemetryPlot` components should now be responsive and display appropriately across various screen sizes. The grid layout adjusts the number of plots per row based on the screen width, and the table becomes scrollable on smaller screens to prevent overflow issues.

Feel free to adjust paddings, margins, and sizing to match your application's design preferences. If you have any further questions or need additional assistance, please let me know!