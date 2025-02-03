import { useState } from "react";
import {
  Box,
  Chip,
  Grid,
  Paper,
  Typography,
  Button,
  TextField,
} from "@material-ui/core";

import { Source } from "./addEventPage";
import { Quote } from "./addQuote";
import { Tag } from "./tagEntities";

interface AddSummaryProps {
  source: Source;
  quote: Quote;
  tags: Tag[];
  addSummary: (summary: Summary) => void;
}

export interface Summary {
  text: string;
}

const MAX_SUMMARY_LENGTH = 256;

export const AddSummary = (props: AddSummaryProps) => {
  const { source, quote, tags, addSummary } = props;
  const [tagsToUse, setTagsToUse] = useState<Tag[]>(tags);
  const [addedTags, setAddedTags] = useState<Tag[]>([]);
  const [summaryText, setSummaryText] = useState<string>("");

  const updateSummaryText = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ): void => {
    // handle controlled text input component
    const value = event.currentTarget.value;
    if (value.length > MAX_SUMMARY_LENGTH) return;

    setSummaryText(value);

    for (const tag of addedTags) {
      // double check that all our tags are still there
      if (!tag.name) continue;
      if (!value.includes(tag.name)) {
        // add this back to tags to use
        setAddedTags((tags) => tags.filter((t) => t.guid !== tag.guid));
        setTagsToUse((tags) => [...tags, tag]);
      }
    }
    for (const tag of tagsToUse) {
      // double check that a tag hasn't been added by hand
      if (!tag.name) continue;
      if (value.includes(tag.name)) {
        // add this to addedTags
        setTagsToUse((tags) => tags.filter((t) => t.guid !== tag.guid));
        setAddedTags((tags) => [...tags, tag]);
      }
    }
  };
  const addTagToSummary = (tag: Tag): void => {
    if (!tag.name) return; // can't add a tag without a name, and shouldn't be here anyways
    if (summaryText.length + tag.name.length > MAX_SUMMARY_LENGTH) return;
    setTagsToUse((tags) => tags.filter((t) => t.guid !== tag.guid));
    setAddedTags((tags) => [...tags, tag]);
    setSummaryText((text) => text + tag.name);
  };

  return (
    <Box component="form" sx={{ padding: 50, minWidth: 400 }}>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <Paper>
            <Typography variant="h3">Original Quote</Typography>
            {quote.text}
          </Paper>
        </Grid>

        <Grid item xs={12} sm={6}>
          <Paper>
            <Typography variant="h3">Summary</Typography>
            <TextField
              id="summary"
              variant="filled"
              label="Summary"
              placeholder="Create Summary"
              multiline
              rows={10}
              value={summaryText}
              onChange={updateSummaryText}
              color={
                summaryText.length === MAX_SUMMARY_LENGTH
                  ? "secondary"
                  : "primary"
              }
            />
            <Typography>
              {summaryText.length}/{MAX_SUMMARY_LENGTH} characters remaining
            </Typography>
            <Button
              variant="contained"
              color="primary"
              onClick={() => addSummary({ text: summaryText })}
            >
              Save Summary
            </Button>
          </Paper>
        </Grid>

        <Grid item xs={12} sm={6}>
          <Paper>
            <Typography variant="h3">Remaining Tags</Typography>
            {tagsToUse.map((tag) => (
              <Chip
                label={tag.name ?? ""}
                onClick={() => addTagToSummary(tag)}
              />
            ))}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
