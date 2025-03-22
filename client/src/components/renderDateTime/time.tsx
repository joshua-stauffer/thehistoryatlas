import { CalendarDate } from "../../graphql/events";

const formatOrdinals = (n: number) => {
  const pr = new Intl.PluralRules("en-US", { type: "ordinal" });
  const suffixes = new Map([
    ["one", "st"],
    ["two", "nd"],
    ["few", "rd"],
    ["other", "th"],
  ]);

  const rule = pr.select(n);
  const suffix = suffixes.get(rule);
  return `${n}${suffix}`;
};

export const monthNameByNumber = new Map([
  [0, "January"],
  [1, "February"],
  [2, "March"],
  [3, "April"],
  [4, "May"],
  [5, "June"],
  [6, "July"],
  [7, "August"],
  [8, "September"],
  [9, "October"],
  [10, "November"],
  [11, "December"],
]);

export const monthNumberByName = new Map([
  ["January", 0],
  ["February", 1],
  ["March", 2],
  ["April", 3],
  ["May", 4],
  ["June", 5],
  ["July", 6],
  ["August", 7],
  ["September", 8],
  ["October", 9],
  ["November", 10],
  ["December", 11],
]);

export const dayMap = new Map([
  [0, "Sunday"],
  [1, "Monday"],
  [2, "Tuesday"],
  [3, "Wednesday"],
  [4, "Thursday"],
  [5, "Friday"],
  [6, "Saturday"],
]);

export const renderDateTime = (date: CalendarDate) => {
  const dateObject = new Date(date.datetime.slice(1));
  switch (date.precision) {
    case 7:
      return renderCentury(dateObject);
    case 8:
      return renderDecade(dateObject);
    case 9:
      return renderYear(dateObject);
    case 10:
      return renderMonth(dateObject);
    case 11:
      return renderDay(dateObject);
    default:
      return renderYear(dateObject);
  }
};

export const renderCentury = (date: Date) => {
  const year = date.getFullYear();
  const century = Math.floor(year / 100) * 100;
  if (year > 0) {
    return `${century}s`;
  } else {
    return `${century}s B.C.E.`;
  }
};

export const renderDecade = (date: Date) => {
  const year = date.getFullYear();
  let decade = Math.floor(year / 10) * 10;
  if (decade > 0) {
    return `${decade}s`;
  } else {
    decade = Math.abs(decade);
    return `${decade}s B.C.E.`;
  }
};

export const renderYear = (date: Date) => {
  let year = date.getFullYear();
  if (year > 0) {
    return `${year}`;
  } else {
    year = Math.abs(year);
    return `${year} B.C.E.`;
  }
};

export const renderMonth = (date: Date) => {
  const year = date.getFullYear();
  const month = monthNameByNumber.get(date.getMonth());
  return `${month} of ${year}`;
};

export const renderDay = (date: Date) => {
  const year = date.getFullYear();
  const month = monthNameByNumber.get(date.getMonth());
  const day = formatOrdinals(date.getDate());
  const weekday = dayMap.get(date.getDay());
  return `${weekday} ${month} ${day}, ${year}`;
};
export const MIN_YEAR = -5000;
export const MAX_YEAR = 2000;
export const buildYearMap = () => {
  const yearRange = Math.floor(MAX_YEAR - MIN_YEAR);
  const minYear = Math.floor(MIN_YEAR);
  const years = Array.from(
    { length: yearRange },
    (_, i) => i + minYear + 1,
  ).reverse();

  const optionMap = new Map<string, Date>();
  for (const year of years) {
    const century = `${year}`.padStart(4, "0");
    const date = new Date(year, 1, 1);
    const dateString = renderYear(date);
    optionMap.set(dateString, date);
  }
  return optionMap;
};
export const buildDayMap = () => {
  const days = Array.from({ length: 31 }, (_, i) => i + 1);
  return new Map<string, number>(days.map((day) => [String(day), day]));
};
