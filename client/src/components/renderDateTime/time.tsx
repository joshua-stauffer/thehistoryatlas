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

const monthMap = new Map([
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

const dayMap = new Map([
  [0, "Sunday"],
  [1, "Monday"],
  [2, "Tuesday"],
  [3, "Wednesday"],
  [4, "Thursday"],
  [5, "Friday"],
  [6, "Saturday"],
]);

export const renderDateTime = (date: CalendarDate) => {
  const dateObject = new Date(date.time);
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

const renderCentury = (date: Date) => {
  const year = date.getFullYear();
  let century = Math.floor(year / 100);
  if (century > 0) {
    century += 1;
    const formattedCentury = formatOrdinals(century);
    return `The ${formattedCentury} century`;
  } else {
    century = Math.abs(century);
    const formattedCentury = formatOrdinals(century);
    return `The ${formattedCentury} century B.C.E.`;
  }
};

const renderDecade = (date: Date) => {
  const year = date.getFullYear();
  let decade = Math.floor(year / 10) * 10;
  if (decade > 0) {
    return `The ${decade}s`;
  } else {
    decade = Math.abs(decade);
    return `The ${decade}s B.C.E.`;
  }
};

const renderYear = (date: Date) => {
  const year = date.getFullYear();
  return `The year ${year}`;
};

const renderMonth = (date: Date) => {
  const year = date.getFullYear();
  const month = monthMap.get(date.getMonth());
  return `${month} of ${year}`;
};

const renderDay = (date: Date) => {
  const year = date.getFullYear();
  const month = monthMap.get(date.getMonth());
  const day = formatOrdinals(date.getDate());
  const weekday = dayMap.get(date.getDay());
  return `${weekday} ${month} ${day}, ${year}`;
};
