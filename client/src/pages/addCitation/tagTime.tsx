import { useState } from 'react'
import { Box, Button, Grid, Paper, TextField } from '@material-ui/core'
import CloseIcon from '@mui/icons-material/Close';
import { Tag } from './tagEntities'
import { GET_GUIDS_BY_NAME, GUIDsByNameResult, GUIDsByNameVars } from '../../graphql/getGUIDsByName'
import { useQuery } from '@apollo/client';
import { v4 } from 'uuid';
import { useEffect } from 'react';

interface TagTimeProps {
  text: string;
  setCurrentEntity: React.Dispatch<React.SetStateAction<Tag | null>>;
}

const days = Array.from({ length: 31 }, (_, i) => i + 1)
const months = Array.from({ length: 12 }, (_, i) => i + 1)
const years = Array.from({ length: 2023 }, (_, i) => i + 1).reverse()
const getDefaultYear = (text: string): string | null  => {
  for (const year of years) {
    if (text.includes(String(year))) {
      return String(year)
    }
  }
  return null
}

export const TagTime = (props: TagTimeProps) => {
  const { text, setCurrentEntity } = props;
  const [year, setYear] = useState<string | null>(getDefaultYear(text))
  const [month, setMonth] = useState<string | null>(null)
  const [day, setDay] = useState<string | null>(null)
  const [specificity, setSpecificity] = useState<0 | 1 | 2>(0)

  // check backend for a guid associated with this time tag
  const timeTagName =
    day ? `${year}|${month}|${day}`
      : month ? `${year}|${month}`
        : `${year}`
  const {
    data, loading, error
  } = useQuery<GUIDsByNameResult, GUIDsByNameVars>(GET_GUIDS_BY_NAME,
    { variables: { name: timeTagName } }
  )

  useEffect(() => {
    // on load, update entity to have year
    setCurrentEntity(entity => {
      if (!entity) return entity
      if (!year) return entity
      return {
        ...entity,
        name: year
      }
    })
  }, [])

  useEffect(() => {
    if (loading || error || !data) return
    if (!year) return
    // TODO: handle error
    // set tag GUID
    const guids = data.GetGUIDsByName.guids
    if (guids.length) {
      setCurrentEntity(entity => {
        // each time name should be unique, so take the first one
        return {
          ...entity,
          guid: guids[0]
        } as Tag
      })
    } else {
      setCurrentEntity(entity => {
        // create a new GUID for this tag
        return {
          ...entity,
          guid: "new-" + v4()
        } as Tag
      })
    }
  }, [data, loading, error, year])

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
  const closeMonth = () => {
    setMonth(null)
    setDay(null)
    setSpecificity(0)
    setCurrentEntity(entity => {
      if (!entity?.name) return entity
      const time = entity.name.split('|')
      return {
        ...entity,
        name: time[0]
      }
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
  const closeDay = () => {
    setDay(null)
    setSpecificity(1)
    setCurrentEntity(entity => {
      if (!entity?.name) return entity
      const time = entity.name.split('|')
      return {
        ...entity,
        name: `${time[0]}|${time[1]}`
      }
    })
  }

  return (
    <Box
      component="form"
      sx={{ padding: 50 }}
    >
      <Grid container spacing={2}>
        <Grid item xs={4}>
          <Paper>
            <TextField
              id="pubYear"
              label="Add Year"
              value={year}
              onChange={e => handleYear(e.target.value)}
              select
              SelectProps={{
                native: true,
              }}
            >
              {years.map((year) =>
                <option key={year} value={year}>
                  {year}
                </option>
              )
              }
            </TextField>
          </Paper>
        </Grid>


        <Grid item xs={4}>
          <Paper>
            {specificity > 0 ?
              <>
                <TextField
                  id="pubMonth"
                  label="Add Month"
                  value={month}
                  onChange={e => handleMonth(e.target.value)}
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
                <Button onClick={closeMonth}><CloseIcon /></Button>
              </>
              : <Button onClick={() => setSpecificity(1)}>Add Month</Button>
            }
          </Paper>
        </Grid>




        <Grid item xs={4}>
          <Paper>
            {specificity > 1 ?
              <>
                <TextField
                  id="pubDay"
                  label="Add Day"
                  value={day}
                  onChange={e => handleDay(e.target.value)}
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
                <Button onClick={closeDay}><CloseIcon /></Button>
              </>
              : <Button onClick={() => setSpecificity(2)}>Add Day</Button>
            }
          </Paper>
        </Grid>


      </Grid>
    </Box>
  )
}
