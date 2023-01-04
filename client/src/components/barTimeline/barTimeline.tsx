import { Datum } from "../timeline";
import { ChartHeader, Container } from "./style";
import { Bar } from "./Bar";

interface TimelineProps {
  data: {
    count: number;
    year: number;
    root_guid: string;
  }[];
  currentDate: string | null;
  handleTimelineClick: (guid: string) => void;
}

export const BarTimeline = (props: TimelineProps) => {
  const { data, currentDate, handleTimelineClick } = props;

  // base array for our display data
  const visArr: Datum[] = [];

  // the
  let dateString: string = "";
  if (currentDate) {
    const dateArr = currentDate.split("|");
    dateString = dateArr[0];
  }
  const dateNum = dateString ? Number(dateString) : 0;
  const startYear = dateNum - 50;
  const endYear = dateNum + 50;
  console.log(dateNum);
  // find the appropriate start index in the array
  const startIndex = data.findIndex((d) => Number(d.year) >= startYear);
  let i = startIndex > 0 ? startIndex : 0;
  let maxCount = 0;
  if (data) {
    for (let year = startYear; year < endYear; year++) {
      if (i < data.length - 1 && data[i].year === year) {
        visArr.push(data[i]);
        i++;
        if (data[i].count > maxCount) maxCount = data[i].count;
      } else {
        visArr.push({
          count: 0,
          year: year,
          root_guid: "",
        });
      }
    }
  }

  console.log(visArr);
  return (
    <Container>
      <ChartHeader>Number of Events By Year</ChartHeader>
      <svg width={600} height={150}>
        <text x={0} y={10}>
          ( Max: {maxCount} )
        </text>
        {visArr.map((datum, i) => (
          <Bar
            index={i}
            count={datum.count}
            guid={datum.root_guid}
            maxCount={maxCount > 5 ? maxCount : 5}
            onClick={handleTimelineClick}
            totalHeight={100}
            width={5}
            year={datum.year}
          />
        ))}
      </svg>
    </Container>
  );
};

/*
  let dateString: string = '';
  if (currentDate) {
    const dateArr = currentDate.split('|')
    dateString = dateArr[0]
  }
  const curIndex = data.findIndex(d => String(d.year) === dateString)
  

  */
