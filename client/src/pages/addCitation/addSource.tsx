import { useState } from 'react';
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Grid from '@mui/material/Grid'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { v4 } from 'uuid';
import { theme } from '../../baseStyle'

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
  const [title, setTitle] = useState<string>('')
  const [author, setAuthor] = useState<string>('')
  const [publisher, setPublisher] = useState<string>('')
  const [pageNum, setPageNum] = useState<string>('')
  const [pubYear, setPubYear] = useState('')
  const [pubMonth, setPubMonth] = useState('')
  const [pubDay, setPubDay] = useState('')
  const [GUID] = useState(v4())

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
  const days = Array.from({ length: 31 }, (_, i) => i + 1)
  const months = Array.from({ length: 12 }, (_, i) => i + 1)
  const years = Array.from({ length: 2023 }, (_, i) => i + 1)

  return (
    <Box
      component="form"
      sx={{
        paddingTop: 10,
        maxWidth: 300,
        marginLeft: 'auto',
        marginRight: 'auto'
      }}
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
            sx={{color: theme.palette.primary.main}}
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
            {years.reverse().map((year) =>
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
            {months.map((month) =>
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
            {days.map((day) =>
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