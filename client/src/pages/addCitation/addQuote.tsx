import { useState } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Grid from "@mui/material/Grid";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { theme } from "../../baseStyle";

export interface Quote {
  text: string;
}

interface AddQuoteProps {
  addQuote: (quote: Quote) => void;
}

export const AddQuote = (props: AddQuoteProps) => {
  const [text, setText] = useState<string>("");
  const { addQuote } = props;
  const validateInput = () => text.length > 0;
  return (
    <Box
      component="form"
      sx={{
        padding: 10,
        maxWidth: 300,
        marginLeft: "auto",
        marginRight: "auto",
      }}
    >
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Typography>Add Citation Text</Typography>
        </Grid>

        <Grid item xs={12}>
          <TextField
            multiline
            minRows={5}
            variant="filled"
            id="text"
            label="Citation Text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            sx={{ color: theme.palette.primary.main }}
          />
        </Grid>

        <Button
          disabled={!validateInput()}
          variant="contained"
          onClick={() => addQuote({ text })}
        >
          Save & Continue
        </Button>
      </Grid>
    </Box>
  );
};
