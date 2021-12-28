import { useState } from 'react';
import { Box, Button, Grid, TextField, Typography } from "@material-ui/core";
import { v4 } from 'uuid';

export interface Source {
  title: string
  author: string
  publisher: string
  pubDate?: string
  pageNum?: number
  GUID: string
}

interface AddSourceProps {
  addSource: (source: Source) => void;
}

export const AddSource = (props: AddSourceProps) => {
  const { addSource } = props;
  const [ title, setTitle ] = useState<string>('')
  const [ author, setAuthor ] = useState<string>('')
  const [ publisher, setPublisher ] = useState<string>('')
  const [ pageNum, setPageNum ] = useState<string>('')
  const [ pubYear, setPubYear ] = useState('')
  const [ pubMonth, setPubMonth ] = useState('')
  const [ pubDay, setPubDay ] = useState('')
  const [ GUID ] = useState(v4())

  const validateInput = (): boolean => !!title && !!author && !!publisher;
  const saveSource = () => {
    addSource({
      GUID: GUID,
      title: title,
      author: author,
      publisher: publisher,
      pubDate: pubYear && pubMonth && pubDay 
        ? `${pubYear}-${pubMonth}-${pubDay}`
        : undefined
    })
  }
  const days = Array.from({length: 31}, (_, i) => i + 1)
  const months = Array.from({length: 12}, (_, i) => i + 1)
  const years = Array.from({length: 2021}, (_, i) => i + 1)

  return (
    <Box 
      component="form"
      sx={{ padding: 50, maxWidth: 500 }}
    >
      <Grid container spacing={2}>

        <Grid item xs={12}>
          <Typography>
            Save a Source
          </Typography>
        </Grid>

        <Grid item xs={12}>
          <TextField 
            id="title"
            label="Title"
            value={title}
            onChange={e => setTitle(e.target.value)}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField 
            id="author"
            label="Author"
            value={author}
            onChange={e => setAuthor(e.target.value)}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField 
            id="publisher"
            label="Publisher"
            value={publisher}
            onChange={e => setPublisher(e.target.value)}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField 
            id="pageNum"
            label="Page Number"
            value={pageNum}
            onChange={e => setPageNum(e.target.value)}
          />
        </Grid>

      <Grid item xs={4}>
        <TextField 
          id="pubYear"
          label="Year Published"
          value={pubYear}
          onChange={e => setPubYear(e.target.value)}
          select
          SelectProps={{
            native: true,
          }}
        >
          { years.reverse().map((year) => 
              <option key={year} value={year}>
                {year}
            </option>
            )
          }
        </TextField>
      </Grid>

      <Grid item xs={4}>
        <TextField 
          id="pubMonth"
          label="Month Published"
          value={pubMonth}
          onChange={e => setPubMonth(e.target.value)}
          select
          SelectProps={{
            native: true,
          }}
        >
          { months.map((month) => 
              <option key={month} value={month}>
                {month}
            </option>
            )
          }
        </TextField>
      </Grid>

      <Grid item xs={4}>
        <TextField 
          id="pubDay"
          label="Day Published"
          value={pubDay}
          onChange={e => setPubDay(e.target.value)}
          select
          SelectProps={{
            native: true,
          }}
        >
          { days.map((day) => 
              <option key={day} value={day}>
                {day}
            </option>
            )
          }
        </TextField>
        </Grid>

        <Grid item xs={12}>
        <Button
          disabled={!validateInput()}
          variant="contained"
          onClick={saveSource}
        >
          Save & Continue
        </Button>
        </Grid>

      </Grid>
    </Box>
  )
}