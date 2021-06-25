import { useRef } from 'react'
import { select } from 'd3-selection';
import { axisBottom, axisLeft } from 'd3-axis';
import { Dimensions } from './timeline'


interface XAxisProps {
  dimensions: Dimensions;
  scale: d3.ScaleTime<number, number, never>;
}

export const XAxis = (props: XAxisProps) => {
  const { dimensions, scale } = props;
  const ref = useRef<SVGGElement>(null)

  if (ref.current) {
    select(ref.current)
      .transition()
      .call(axisBottom(scale).ticks(5))
    .select(".domain").remove()
  }

  return (
    <g
      className={"g2"}
      ref={ref}
      transform={`translate(0, 75)`}
    >
    </g>
  )
}

interface YAxisProps {
  scale: d3.ScaleLinear<number, number, never>;
  dimensions: Dimensions
}

export const YAxis = (props: YAxisProps) => {
  const { scale } = props;
  const ref = useRef<SVGGElement>(null)

  
  if (ref.current) {
    select(ref.current)
      .transition()
      .call(axisLeft(scale))
  }
  const ticks = scale.ticks(10)

  return (
    <g 
      ref={ref}
    />
  )
}