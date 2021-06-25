


interface BarProps {
  index: number;
  width: number;
  totalHeight: number;
  count: number;
  maxCount: number;
  onClick: (guid: string) => void;
  guid: string;
  year: number;
}

export const Bar = (props: BarProps) => {
  const { index, width, totalHeight, count, maxCount, onClick, guid, year } = props;
  const barHeight = ((count / maxCount) * totalHeight) || 1;
  const barOffset = totalHeight - barHeight
  const paddingLeft = 65;
  const xLabelOffset = -10;
  if (index % 25 !== 0 && index < 99) {
    return (
      <rect
        x={index * width + paddingLeft}
        y={barOffset -30}
        width={width}
        height={barHeight}
        stroke={'#111'}
        onClick={() => guid === '' ? () => console.log('clicked') : onClick(guid)}
        ry={10}
        rx={0}
        fillOpacity={0.4}
      />
    )
  }
  return (
    <>
    <rect
      x={((index) * width) + paddingLeft}
      y={barOffset - 30}
      width={width}
      height={barHeight}
      stroke={'#111'}
      onClick={() => guid === '' ? () => console.log('clicked') : onClick(guid)}
      ry={10}
      rx={0}
    />
    <text
      x={index * width + paddingLeft + xLabelOffset}
      y={90}
    >
      {year}
    </text>
    </>
  )
}

//transform={`translate(${index * width}, ${totalHeight})`}

/*
    key={index}
    x={index * width}
    y={0}
    width={width}
    height={100}
    stroke={'#111'}
    onClick={() => guid === '' ? () => console.log('clicked') : onClick(guid)}
    fill={'#111'}
    strokeWidth={5}

    */