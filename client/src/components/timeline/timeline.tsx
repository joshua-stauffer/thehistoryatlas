import { useEffect } from "react";
import * as d3 from "d3";
import { extent, timeParse, line } from "d3";
import { scaleTime, scaleLinear } from "d3-scale";
import { useRef } from "react";
import { GetManifestResult } from "../../graphql/getManifest";
import { Container } from "./style";
import { XAxis, YAxis } from "./axis";
//GetManifestResult["GetManifest"]["timeline"]
interface TimelineProps {
  data: {
    count: number;
    year: number;
    root_guid: string;
  }[];
  currentDate: string | null;
  handleTimelineClick: (guid: string) => void;
}

export interface Dimensions {
  width: number;
  height: number;
  marginTop: number;
  marginBottom: number;
  marginRight: number;
  marginLeft: number;
  boundedHeight: number;
  boundedWidth: number;
}

export interface Datum {
  count: number;
  year: number;
  root_guid: string;
}

export const Timeline = (props: TimelineProps) => {
  const { data, currentDate, handleTimelineClick } = props;
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<SVGAElement>(null);

  const dimensions = {
    // hard coding for now
    width: containerRef.current ? containerRef.current.offsetWidth : 0,
    height: containerRef.current ? containerRef.current.offsetHeight : 0,
    marginTop: 0,
    marginBottom: 0,
    marginLeft: 30,
    marginRight: 0,
    boundedHeight: containerRef.current
      ? containerRef.current.offsetHeight - 30
      : 40,
    boundedWidth: containerRef.current
      ? containerRef.current.offsetWidth + 40
      : 40,
  };
  const dateParser = timeParse("%Y");
  const xAccessor = (datum: Datum) => {
    const date = dateParser(String(datum.year));
    if (!date) return new Date();
    return date;
  };
  const yAccessor = (datum: Datum) => datum.count;

  const xScale = d3
    .scaleTime()
    .domain(d3.extent(data, xAccessor) as any)
    .range([0, dimensions.boundedWidth]);

  const yScale = d3
    .scaleLinear()
    .domain(d3.extent(data, yAccessor) as any)
    .range([dimensions.boundedHeight, 0])
    .nice();

  const yAccessorScaled = (datum: Datum) => yScale(yAccessor(datum));
  const xAccessorScaled = (datum: Datum) => xScale(xAccessor(datum));

  const lineGenerator = line()
    .x((d) => xAccessorScaled(d as any))
    .y((d) => yAccessorScaled(d as any));

  console.log(yScale.ticks());

  useEffect(() => console.log("dimensions are ", dimensions));
  return (
    <Container ref={containerRef}>
      <svg
        className="timeline"
        width={dimensions.width}
        height={dimensions.height}
      >
        <g
          className={"g1"}
          transform={`translate(${dimensions.marginLeft}, ${dimensions.marginTop})`}
          ref={chartRef}
        >
          <XAxis scale={xScale} dimensions={dimensions} />
          <YAxis scale={yScale} dimensions={dimensions} />
          <path
            d={lineGenerator(data as any) as string}
            fill={"none"}
            stroke={"#111"}
            strokeWidth={2}
          />
        </g>
      </svg>
    </Container>
  );
};
