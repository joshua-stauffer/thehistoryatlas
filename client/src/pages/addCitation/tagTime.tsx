import { useState } from 'react'
import { Box, Button, Grid, TextField } from '@material-ui/core'
import { Tag } from './tagEntities'

interface TagTimeProps {
  setCurrentEntity: React.Dispatch<React.SetStateAction<Tag | null>>
}

const days = Array.from({length: 31}, (_, i) => i + 1)
const months = Array.from({length: 12}, (_, i) => i + 1)
const years = Array.from({length: 2021}, (_, i) => i + 1)

export const TagTime = (props: TagTimeProps) => {
  const { setCurrentEntity } = props;
  const [ year, setYear ] = useState<string | null>(null)
  const [ month, setMonth ] = useState<string | null>(null)
  const [ day, setDay ] = useState<string | null>(null)
  const [ specificity, setSpecificity ] = useState<0 | 1 | 2>(0)
  const handleYear = (year: string): void => {
    setYear(year)
    setCurrentEntity(entity => {
      return {
        ...entity,
        name: year
      } as Tag
    })
  }
  const handleMonth = (month: string): void => {
    setMonth(month)
    setCurrentEntity(entity => {
      return {
        ...entity,
        name: `${year}|${month}`
      } as Tag
    })
  }
  const handleDay = (day: string): void => {
    setDay(day)
    setCurrentEntity(entity => {
      return {
        ...entity,
        name: `${year}|${month}|${day}`
      } as Tag
    })
  }

  return (
    <Box 
      component="form"
      sx={{ padding: 50, maxWidth: 500 }}
    >
      <Grid container spacing={2}>
      <Grid item xs={4}>
        <TextField 
          id="pubYear"
          label="Year Published"
          value={year}
          onChange={e => handleYear(e.target.value)}
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

      { specificity > 0 ?
        <Grid item xs={4}>
        <TextField 
          id="pubMonth"
          label="Month Published"
          value={month}
          onChange={e => handleMonth(e.target.value)}
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
      : <Button onClick={() => setSpecificity(1)}>Add Month</Button>
      }

      { specificity > 1 ?
      <Grid item xs={4}>
        <TextField 
          id="pubDay"
          label="Day Published"
          value={day}
          onChange={e => handleDay(e.target.value)}
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
        : <Button onClick={() => setSpecificity(2)}>Add Day</Button>
      }

      </Grid>
    </Box>
  )
}