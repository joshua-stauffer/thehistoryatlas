import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  TextField,
} from "@mui/material";
import React, { useEffect, useState } from "react";
import { FormControl } from "@material-ui/core";
import Autocomplete from "@mui/material/Autocomplete";
import {
  buildDayMap,
  buildYearMap,
  MAX_YEAR,
  MIN_YEAR,
  monthNumberByName,
  renderCentury,
  renderDecade,
} from "../../components/renderDateTime/time";

interface TimeTravelModalProps {
  isOpen: boolean;
  handleClose: () => void;
}

export const TimeTravelModal = (props: TimeTravelModalProps) => {
  const [precision, setPrecision] = useState<7 | 8 | 9 | 10 | 11>(7);
  const [timestamp, setTimestamp] = useState<Date | null>(null);
  const handlePrecisionChange = (event: SelectChangeEvent) => {
    setTimestamp(null); // clear existing date
    const parsedNumber = Number(event.target.value);
    let newPrecision: 7 | 8 | 9 | 10 | 11;
    switch (parsedNumber) {
      case 7:
        newPrecision = 7;
        break;
      case 8:
        newPrecision = 8;
        break;
      case 9:
        newPrecision = 9;
        break;
      case 10:
        newPrecision = 10;
        break;
      case 11:
        newPrecision = 11;
        break;
      default:
        newPrecision = 7;
    }
    setPrecision(newPrecision);
  };
  return (
    <Dialog open={props.isOpen} onClose={props.handleClose}>
      <DialogTitle>Time Travel</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Jump to the event in the current story closest to the chosen time.
        </DialogContentText>
        <FormControl variant={"standard"}>
          <InputLabel id="select-time-precision-label">
            Time Precision
          </InputLabel>
          <Select
            labelId="select-time-precision-label"
            id="select-time-precision"
            value={String(precision)}
            label={"Time Precision"}
            onChange={handlePrecisionChange}
            sx={{ margin: 2 }}
          >
            <MenuItem value={11}>Day</MenuItem>
            <MenuItem value={10}>Month</MenuItem>

            <MenuItem value={9}>Year</MenuItem>
            <MenuItem value={8}>Decade</MenuItem>

            <MenuItem value={7}>Century</MenuItem>
          </Select>
        </FormControl>
      </DialogContent>
      <DialogContent>
        <FormControl>
          {precision === 7 ? (
            <CenturyPrecision
              timestamp={timestamp}
              setTimestamp={(timestamp) => setTimestamp(timestamp)}
            />
          ) : precision === 8 ? (
            <DecadePrecision
              timestamp={timestamp}
              setTimestamp={(timestamp) => setTimestamp(timestamp)}
            />
          ) : precision === 9 ? (
            <YearPrecision
              timestamp={timestamp}
              setTimestamp={(timestamp) => setTimestamp(timestamp)}
            />
          ) : precision === 10 ? (
            <MonthPrecision
              timestamp={timestamp}
              setTimestamp={(timestamp) => setTimestamp(timestamp)}
            />
          ) : precision === 11 ? (
            <DayPrecision
              timestamp={timestamp}
              setTimestamp={(timestamp) => setTimestamp(timestamp)}
            />
          ) : null}
        </FormControl>
      </DialogContent>
      <DialogActions>
        <Button onClick={props.handleClose}>Cancel</Button>
        <Button onClick={props.handleClose} disabled={!timestamp}>
          Go
        </Button>
      </DialogActions>
    </Dialog>
  );
};

interface TimePrecisionProps {
  timestamp: Date | null;
  setTimestamp: React.Dispatch<React.SetStateAction<Date | null>>;
}

const CenturyPrecision = (props: TimePrecisionProps) => {
  const centuryRange = Math.floor((MAX_YEAR - MIN_YEAR) / 100);
  const minCentury = Math.floor(MIN_YEAR / 100);
  const centuries = Array.from(
    { length: centuryRange },
    (_, i) => (i + minCentury + 1) * 100
  ).reverse();

  const optionMap = new Map<string, Date>();
  for (const year of centuries) {
    const century = `${year}`.padStart(4, "0");
    const date = new Date(year, 1, 1);
    const dateString = renderCentury(date);
    optionMap.set(dateString, date);
  }

  const handleSelectCentury = (century: string | null): void => {
    const timestamp = optionMap.get(century || "");
    props.setTimestamp(timestamp ? timestamp : null);
  };

  return (
    <Autocomplete
      id="select-century"
      options={Array.from(optionMap.keys())}
      sx={{ width: 300, margin: 3 }}
      onChange={(event: any, newValue: string | null) => {
        handleSelectCentury(newValue);
      }}
      renderInput={(params) => <TextField {...params} label="Century" />}
    />
  );
};

const DecadePrecision = (props: TimePrecisionProps) => {
  const decadeRange = Math.floor((MAX_YEAR - MIN_YEAR) / 10);
  const minDecade = Math.floor(MIN_YEAR / 10);
  const decades = Array.from(
    { length: decadeRange },
    (_, i) => (i + minDecade + 1) * 10
  ).reverse();

  const optionMap = new Map<string, Date>();
  for (const year of decades) {
    const century = `${year}`.padStart(4, "0");
    const date = new Date(year, 1, 1);
    const dateString = renderDecade(date);
    optionMap.set(dateString, date);
  }

  const handleSelectDecade = (decade: string | null): void => {
    const timestamp = optionMap.get(decade || "");
    props.setTimestamp(timestamp ? timestamp : null);
  };

  return (
    <Autocomplete
      id="select-decade"
      options={Array.from(optionMap.keys())}
      sx={{ width: 300, margin: 3 }}
      onChange={(event: any, newValue: string | null) => {
        handleSelectDecade(newValue);
      }}
      renderInput={(params) => <TextField {...params} label="Decade" />}
    />
  );
};

const YearPrecision = (props: TimePrecisionProps) => {
  const optionMap = buildYearMap();
  const handleSelectYear = (year: string | null): void => {
    const timestamp = optionMap.get(year || "");
    props.setTimestamp(timestamp ? timestamp : null);
  };

  return (
    <Autocomplete
      id="select-year"
      options={Array.from(optionMap.keys())}
      sx={{ width: 300, margin: 3 }}
      onChange={(event: any, newValue: string | null) => {
        handleSelectYear(newValue);
      }}
      renderInput={(params) => <TextField {...params} label="Year" />}
    />
  );
};

const MonthPrecision = (props: TimePrecisionProps) => {
  const yearMap = buildYearMap();

  const [year, setYear] = useState<Date | null>(null);
  const [month, setMonth] = useState<number | null>(null);

  const handleSelectYear = (year: string | null): void => {
    const timestamp = yearMap.get(year || "") || null;
    setYear(timestamp);
  };
  const handleSelectMonth = (month: string | null): void => {
    if (month === null) {
      setMonth(null);
    } else {
      const monthNumber = monthNumberByName.get(month);
      setMonth(monthNumber === undefined ? null : monthNumber);
    }
  };
  useEffect(() => {
    // if all values have been selected, update timestamp
    if (year === null || month === null) return;
    year.setMonth(month);
    props.setTimestamp(year);
  }, [year, month]);
  return (
    <>
      <Autocomplete
        id="select-year"
        options={Array.from(yearMap.keys())}
        sx={{ width: 300, margin: 3 }}
        onChange={(event: any, newValue: string | null) => {
          handleSelectYear(newValue);
        }}
        renderInput={(params) => <TextField {...params} label="Year" />}
      />
      <Autocomplete
        id="select-month"
        options={Array.from(monthNumberByName.keys())}
        sx={{ width: 300, margin: 3 }}
        onChange={(event: any, newValue: string | null) => {
          handleSelectMonth(newValue);
        }}
        renderInput={(params) => <TextField {...params} label="Month" />}
      />
    </>
  );
};

const DayPrecision = (props: TimePrecisionProps) => {
  const [year, setYear] = useState<Date | null>(null);
  const [month, setMonth] = useState<number | null>(null);
  const [day, setDay] = useState<number | null>(null);

  const yearMap = buildYearMap();
  const dayMap = buildDayMap();

  const handleSelectYear = (year: string | null): void => {
    if (year === null) {
      setMonth(null);
    } else {
      const timestamp = yearMap.get(year);
      setYear(timestamp === undefined ? null : timestamp);
    }
  };

  const handleSelectMonth = (month: string | null): void => {
    if (month === null) {
      setMonth(null);
    } else {
      const monthNumber = monthNumberByName.get(month);
      setMonth(monthNumber === undefined ? null : monthNumber);
    }
  };
  const handleSelectDay = (day: string | null): void => {
    if (day === null) {
      setDay(null);
    } else {
      const dayNumber = dayMap.get(day);
      setDay(dayNumber === undefined ? null : dayNumber);
    }
  };

  useEffect(() => {
    // if all values have been selected, update timestamp
    if (year === null || month === null || day === null) return;
    year.setMonth(month);
    year.setDate(day);
    props.setTimestamp(year);
  }, [year, month, day]);

  return (
    <>
      <Autocomplete
        id="select-year"
        options={Array.from(yearMap.keys())}
        sx={{ width: 300, margin: 3 }}
        onChange={(event: any, newValue: string | null) => {
          handleSelectYear(newValue);
        }}
        renderInput={(params) => <TextField {...params} label="Year" />}
      />
      <Autocomplete
        id="select-month"
        options={Array.from(monthNumberByName.keys())}
        sx={{ width: 300, margin: 3 }}
        onChange={(event: any, newValue: string | null) => {
          handleSelectMonth(newValue);
        }}
        renderInput={(params) => <TextField {...params} label="Month" />}
      />
      <Autocomplete
        id="select-day"
        options={Array.from(dayMap.keys())}
        sx={{ width: 300, margin: 3 }}
        onChange={(event: any, newValue: string | null) => {
          handleSelectDay(newValue);
        }}
        renderInput={(params) => <TextField {...params} label="Day" />}
      />
    </>
  );
};
