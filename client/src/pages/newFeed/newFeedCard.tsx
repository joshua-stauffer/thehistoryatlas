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
  Chip,
} from "@mui/material";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { EventItem, Focus, Tag } from "../../graphql/events";
import { Box } from "@material-ui/core";
import { renderDateTime } from "../../components/renderDateTime/time";
import { GoPerson } from "react-icons/go";
import { VscLocation } from "react-icons/vsc";
import { BiTimeFive } from "react-icons/bi";

interface NewFeedCardProps {
  event: EventItem;
}

export const NewFeedCard = (props: NewFeedCardProps) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const toggleIsOpen = () => setIsOpen((current) => !current);
  console.log(buildTaggedText(props.event));
  return (
    <Card sx={{ margin: "30px" }}>
      <CardHeader
        sx={{ textAlign: "center" }}
        title={buildCurrentFocus(props.event.focus)}
        subheader={renderDateTime(props.event.date)}
      />
      <CardActions disableSpacing>
        <IconButton sx={{ marginLeft: "auto", marginRight: "auto" }}>
          <ArrowBackIcon />
        </IconButton>
        <IconButton sx={{ marginLeft: "auto", marginRight: "auto" }}>
          <ArrowForwardIcon />
        </IconButton>
      </CardActions>

      <CardContent>
        <Typography
          paragraph
          gutterBottom
          textAlign="center"
          sx={{
            marginTop: 5,
            marginBottom: 5,
          }}
        >
          {buildTaggedText(props.event)}
        </Typography>
      </CardContent>
      <CardContent sx={{ marginLeft: "40px" }}>
        <Typography paragraph>"{props.event.source.text}"</Typography>
        <Typography paragraph>
          -- {props.event.source.title} ({props.event.source.author})
        </Typography>
      </CardContent>
    </Card>
  );
};

const buildCurrentFocus = (focus: Focus | null) => {
  if (!focus) {
    return "Events in the history of the world";
  } else if (focus.type === "PERSON") {
    return `Events in the life of ${focus.name}`;
  } else {
    return `Events in the history of ${focus.name}`;
  }
};

const buildTaggedText = (event: EventItem): (string | JSX.Element | null)[] => {
  let tagIndices: Array<number> = [];
  for (const tag of event.tags) {
    const indices = Array.from(
      { length: tag.stopChar - tag.startChar },
      (_, i) => tag.startChar + i
    );
    tagIndices = [...tagIndices, ...indices];
  }
  const tagIndicesSet = new Set(tagIndices);
  console.log(tagIndicesSet);
  const startCharMap: Map<number, Tag> = new Map(
    event.tags.map((tag) => [tag.startChar, tag])
  );
  const text = Array.from(event.text).map((char, index) => {
    const tag = startCharMap.get(index);
    if (!!tag) {
      return (
        <Chip
          label={tag.name}
          icon={
            tag.type === "PERSON" ? (
              <GoPerson />
            ) : tag.type === "PLACE" ? (
              <VscLocation />
            ) : (
              <BiTimeFive />
            )
          }
          variant={"outlined"}
        />
      );
    } else if (tagIndicesSet.has(index)) {
      return null;
    } else {
      return char;
    }
  });
  console.log(text);
  return text;
};
