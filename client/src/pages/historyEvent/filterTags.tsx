import { Grid, Chip } from "@mui/material";
import { Person, Place, Timer } from "@mui/icons-material";

import { addToHistoryProps } from "../../hooks/history";
import { Focus, Tag } from "../../graphql/events";

interface FilterTagProps {
  filters: Focus[];
}

export const FilterTags = (props: FilterTagProps) => {
  return (
    <Grid container justifyContent={"space-around"}>
      {props.filters.map((tag) => (
        <Grid item xs>
          <Chip
            variant={"outlined"}
            icon={tag.type === "PERSON" ? <Person /> : <Place />}
            title={tag.name}
            label={tag.name}
            color={getChipColor(tag)}
          />
        </Grid>
      ))}
    </Grid>
  );
};

type colorOptions = "primary" | "secondary" | "success";
const getChipColor = (tag: Focus): colorOptions => {
  if (tag.type === "PERSON") return "primary";
  if (tag.type === "PLACE") return "secondary";
  return "success";
};
