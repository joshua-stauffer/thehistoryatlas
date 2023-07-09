import { useState } from "react";
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Collapse,
  IconButton,
} from "@mui/material";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import ShareIcon from "@material-ui/icons/Share";
import { EventItem } from "../../graphql/events";

interface NewFeedCardProps {
  event: EventItem;
}

export const NewFeedCard = (props: NewFeedCardProps) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const toggleIsOpen = () => setIsOpen((current) => !current);

  return (
    <Card
      variant={"outlined"}
      sx={{
        minHeight: 150,
      }}
    >
      <CardContent>
        <Typography variant="h6" gutterBottom textAlign="center">
          {props.event.text}
        </Typography>
      </CardContent>
      <CardActions>
        <IconButton>
          <ShareIcon />
        </IconButton>
        <IconButton onClick={toggleIsOpen}>
          <Typography variant="button">Sources</Typography>
          <ExpandMoreIcon />
        </IconButton>
      </CardActions>
      <Collapse in={isOpen} timeout="auto">
        {props.event.sources.map((source) => (
          <>
            <Typography variant={"h2"}>source.title</Typography>
            <Typography>source.text</Typography>
          </>
        ))}
      </Collapse>
    </Card>
  );
};
