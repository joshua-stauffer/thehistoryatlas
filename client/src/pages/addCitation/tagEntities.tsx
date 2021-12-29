import { useState, useEffect } from 'react';
import { useQuery } from '@apollo/client';
import { GET_TEXT_ANALYSIS, TextAnalysisResult, TextAnalysisVars } from '../../graphql/getTextAnalysis'
import { Box, Button, Chip, Grid, Paper, TextField, Typography,
  Radio, RadioGroup, FormLabel, FormControl, FormControlLabel
} from "@material-ui/core";
import { TagTime } from './tagTime';
import { TagPlace } from './tagPlace';
import { TagPerson } from './tagPerson';

export interface Tag {
  start_char: number
  stop_char: number
  name: string
  type: "NONE" | "PERSON" | "PLACE" | "TIME"
  guid?: string
  latitude?: number
  longitude?: number
}

export interface TagEntitiesProps {
  tagEntities: (tags: Tag[]) => void;
  text: string;
}

export const TagEntities = (props: TagEntitiesProps) => {
  const [tags, setTags] = useState<Tag[]>([])
  const [currentEntity, setCurrentEntity] = useState<Tag | null>(null)
  const { tagEntities, text } = props;
  const {
    loading, error, data
  } = useQuery<TextAnalysisResult, TextAnalysisVars>(
    GET_TEXT_ANALYSIS,
    { variables: { text: text } }
  )
  console.log(data)

  const clearTag = (tag: Tag): void => {
    setTags((tags) => {
      const index = tags.indexOf(tag)
      if (index < 0) return tags
      tags[index].type = "NONE"
      return tags
    })
  }
  const saveTag = (tag: Tag): void => {
    setTags((tags) => {
      const index = tags.indexOf(tag)
      if (index < 0) return tags
      tags[index] = tag
      return tags
    })
  }
  const canSaveTag = (tag: Tag): boolean => {
    if (tag.type === "TIME") {
      if (tag.guid) return true
      return false
    }
    else if (tag.type === "PERSON") {
      if (tag.guid) return true
      return false
    }
    else if (tag.type === "PLACE") {
      if (tag.latitude && tag.longitude) return true
      return false
    }
    else { // tag is "NONE"
      return false
    }

  }

  const boundaries = data?.GetTextAnalysis.boundaries
  useEffect(() => {
    if (!boundaries) return
    setTags(boundaries.map((boundary) => {
      return {
        start_char: boundary.start_char,
        stop_char: boundary.stop_char,
        name: boundary.text,
        type: "NONE"
      }
    }))
  }, [data, boundaries])
  if (loading) return <h1>loading..</h1> // replace with real loading screen app wide
  if (error) return <h1>Oops, there was an error: {error}</h1>
  console.log('current entity ', currentEntity)
  return (
    <Box>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <Paper>
            <Typography align="center">Tag Citation</Typography>
            {tags.map((tag) => {
                switch (tag.type) {
                  case "NONE":
                    return (             
                      <Chip 
                        label={tag.name}
                        clickable
                        onClick={() => setCurrentEntity(tag)}
                        variant='outlined'
                      />
                    )
                  case "PERSON":
                    return (             
                      <Chip 
                        label={tag.name}
                        onDelete={() => clearTag(tag)}
                      />
                    )
                  case "PLACE":
                    return (             
                      <Chip 
                        label={tag.name}
                        onDelete={() => clearTag(tag)}
                      />
                    )
                  case "TIME":
                    return (             
                      <Chip 
                        label={tag.name}
                        onDelete={() => clearTag(tag)}
                      />
                    )
                }
              })
            }
          </Paper>
        </Grid>

        <Grid item xs={12} sm={6}>
          <Paper>
            { currentEntity ? 
            <>
            <Typography align="center">Create Tag "{currentEntity.name}"</Typography>
            <FormControl component="fieldset">
              <FormLabel component="legend">Entity Type</FormLabel>
              <RadioGroup 
                row aria-label="entity-type" 
                name="row-radio-buttons-group"
                onChange={(event) => setCurrentEntity(entity => {
                  // save the currentEntity type as the value of the radio button
                  if (!entity) return entity
                  return {
                    ...entity,
                    type: event.target.value
                  } as Tag
                })}
              >
                <FormControlLabel value="PERSON" control={<Radio />} label="Person" />
                <FormControlLabel value="PLACE" control={<Radio />} label="Place" />
                <FormControlLabel value="TIME" control={<Radio />} label="Time" />
              </RadioGroup>
            </FormControl>
            { // render sub component based on current radio value, as saved in currentEntity.type
              currentEntity.type === "PERSON"
              ? <TagPerson setCurrentEntity={setCurrentEntity}/>
              : currentEntity.type === "PLACE"
              ? <TagPlace setCurrentEntity={setCurrentEntity}/>
              : currentEntity.type === "TIME"
              ? <TagTime setCurrentEntity={setCurrentEntity}/>
              : <br/>
            }
            <br/>
            <Button 
              onClick={() => saveTag(currentEntity)}
              disabled={!canSaveTag(currentEntity)}
            >Save</Button>
            <Button onClick={() => setCurrentEntity(null)}>Cancel</Button>
            </>
            : <Typography align="center">Click a word to tag a Person, Place, or Time</Typography>
            }
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Button>Save Tags & Continue</Button>
        </Grid>
      </Grid>
    </Box>
  )
}
