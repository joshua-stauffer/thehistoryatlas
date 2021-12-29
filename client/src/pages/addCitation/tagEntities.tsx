import { useState, useEffect } from 'react';
import { useQuery } from '@apollo/client';
import { GET_TEXT_ANALYSIS, TextAnalysisResult, TextAnalysisVars } from '../../graphql/getTextAnalysis'
import {
  Box, Button, Chip, Grid, Paper, Typography,
  Radio, RadioGroup, FormLabel, FormControl, FormControlLabel
} from "@material-ui/core";
import { TagTime } from './tagTime';
import { TagPlace } from './tagPlace';
import { TagPerson } from './tagPerson';

export interface Tag {
  start_char: number
  stop_char: number
  text: string // represents the value as it is in the citation
  name?: string // represents the user provided label
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

  const tagsAreComplete: boolean =
    !!tags.filter(tag => tag.type === "PERSON").length
    && !!tags.filter(tag => tag.type === "PLACE").length
    && !!tags.filter(tag => tag.type === "TIME").length

  const clearTag = (tag: Tag): void => {
    console.log('clearing tag ', tagsAreComplete)
    setTags((tags) => {
      const index = tags.map(t => t.start_char).indexOf(tag.start_char)
      console.log('index is ', index)
      if (index < 0) return tags
      tags[index].type = "NONE"
      return [...tags] // force react to rerender
    })
  }
  const saveTag = (tag: Tag): void => {
    console.log('save tag is ', tag)
    setTags((tags) => {
      const index = tags.map(t => t.start_char).indexOf(tag.start_char)
      if (index < 0) return tags
      return [...tags.slice(0, index), tag, ...tags.slice(index + 1)]
    })
    setCurrentEntity(null)
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
      if (tag.guid && tag.latitude && tag.longitude) return true
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
        text: boundary.text,
        type: "NONE"
      }
    }))
  }, [data, boundaries])
  if (loading) return <h1>loading..</h1> // replace with real loading screen app wide
  if (error) return <h1>Oops, there was an error: {error}</h1>
  console.log('current entity ', currentEntity)
  console.log('tags ', tags)
  return (
    <Box>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <Paper>
            <Typography align="center">Tag Citation</Typography>
            {
              tags.map(tag =>
                tag.type === "PERSON"
                  ? <Chip
                    label={tag.text}
                    onDelete={() => clearTag(tag)}
                  />
                  : tag.type === "PLACE"
                    ? <Chip
                      label={tag.text}
                      onDelete={() => clearTag(tag)}
                    />
                    : tag.type === "TIME"
                      ? <Chip
                        label={tag.text}
                        onDelete={() => clearTag(tag)}
                      />
                      : <Chip
                        label={tag.text}
                        clickable
                        onClick={() => setCurrentEntity(tag)}
                        variant='outlined'
                      />
              )
            }
          </Paper>
        </Grid>

        <Grid item xs={12} sm={6}>
          <Paper>
            {currentEntity ?
              <>
                <Typography align="center">Create Tag "{currentEntity.text}"</Typography>
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
                    ? <TagPerson currentEntity={currentEntity} setCurrentEntity={setCurrentEntity} />
                    : currentEntity.type === "PLACE"
                      ? <TagPlace setCurrentEntity={setCurrentEntity} />
                      : currentEntity.type === "TIME"
                        ? <TagTime setCurrentEntity={setCurrentEntity} />
                        : <br />
                }
                <br />
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
          <Button
            variant="contained"
            onClick={() => tagEntities(tags.filter(tag => tag.type !== "NONE"))}
            disabled={!tagsAreComplete}
          >Save Tags & Continue</Button>
        </Grid>
      </Grid>
    </Box>
  )
}
