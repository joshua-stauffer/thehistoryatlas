import { useState } from "react";
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Collapse,
  IconButton,
  CardHeader,
  TextField,
} from "@mui/material";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { EventItem } from "../../graphql/events";
import { Box } from "@material-ui/core";
import { renderDateTime } from "../../components/renderDateTime/time";
import { FilterTags } from "./filterTags";
import Autocomplete from "@mui/material/Autocomplete";
import { peopleAndPlaceOptions } from "../../data";

interface NewFeedCardProps {
  event: EventItem;
}

export const NewFeedCard = (props: NewFeedCardProps) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const toggleIsOpen = () => setIsOpen((current) => !current);

  return (
    <Card sx={{ margin: "30px" }}>
      <CardActions disableSpacing>
        <IconButton sx={{ marginLeft: "auto", marginRight: "25px" }}>
          <ArrowBackIcon />
        </IconButton>
        <IconButton sx={{ marginLeft: "25px", marginRight: "auto" }}>
          <ArrowForwardIcon />
        </IconButton>
      </CardActions>
      <CardHeader
        sx={{ textAlign: "center" }}
        title={renderDateTime(props.event.date)}
      ></CardHeader>

      <CardContent>
        <Typography
          paragraph
          gutterBottom
          textAlign="center"
          sx={{
            marginTop: 8,
            marginBottom: 8,
          }}
        >
          {props.event.text}
        </Typography>
      </CardContent>
      <CardContent sx={{ marginLeft: "40px" }}>
        <Typography paragraph>"{props.event.source.text}"</Typography>
        <Typography paragraph>
          -- {props.event.source.title} ({props.event.source.author})
        </Typography>
      </CardContent>
      <CardContent>
        <Autocomplete
          multiple
          id="tags-outlined"
          options={peopleAndPlaceOptions}
          getOptionLabel={(option) => option.name}
          defaultValue={props.event.filters}
          filterSelectedOptions
          renderInput={(params) => (
            <TextField
              {...params}
              label="Filter Events by Person or Place"
              placeholder="Add a Filter"
            />
          )}
        />
      </CardContent>
    </Card>
  );
};
