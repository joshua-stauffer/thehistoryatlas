import { Grid, Chip } from "@mui/material";
import { Person, Place, Timer } from "@mui/icons-material";

import { addToHistoryProps } from "../../hooks/history";
import { Tag } from "../../graphql/events";

interface NewTagBoxProps {
  tags: Tag[];
}

export const NewTagBox = (props: NewTagBoxProps) => {
  return (
    <Grid container justifyContent={"space-around"}>
      {props.tags.map((tag) => (
        <Grid item xs>
          <Chip
            variant={"filled"}
            icon={
              tag.type === "PERSON" ? (
                <Person />
              ) : tag.type === "PLACE" ? (
                <Place />
              ) : (
                <Timer />
              )
            }
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
const getChipColor = (tag: Tag): colorOptions => {
  if (tag.type === "PERSON") return "primary";
  if (tag.type === "PLACE") return "secondary";
  return "success";
};
