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
import { ViewEntity } from './viewEntity';

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

// type DiscoveredEntity = TextAnalysisResult["GetTextAnalysis"]["text_map"]["PERSON"]
//   | TextAnalysisResult["GetTextAnalysis"]["text_map"]["PLACE"]
//   |TextAnalysisResult["GetTextAnalysis"]["text_map"]["TIME"]

interface DiscoveredEntity {
  text: string;
  start_char: number;
  stop_char: number;
  guids: string[];
  coords?: {
      latitude: number;
      longitude: number;
  }[]
}

export interface TagEntitiesProps {
  tagEntities: (tags: Tag[]) => void;
  text: string;
}

export const TagEntities = (props: TagEntitiesProps) => {
  const [tags, setTags] = useState<Tag[]>([])
  const [currentEntity, setCurrentEntity] = useState<Tag | null>(null)
  const [focusedEntity, setFocusedEntity] = useState<Tag | null>(null)
  const [restoreState, setRestoreState] = useState<Tag[] | null>(null)
  const { tagEntities, text } = props;
  const {
    loading, error, data
  } = useQuery<TextAnalysisResult, TextAnalysisVars>(
    GET_TEXT_ANALYSIS,
    { variables: { text: text } }
  )
  console.log({data})

  const tagsAreComplete: boolean =
    !!tags.filter(tag => tag.type === "PERSON").length
    && !!tags.filter(tag => tag.type === "PLACE").length
    && !!tags.filter(tag => tag.type === "TIME").length

  const clearTag = (tag: Tag): void => {
    setTags((tags) => {
      const index = tags.map(t => t.start_char).indexOf(tag.start_char)
      if (index < 0) return tags
      tags[index].type = "NONE"
      return [...tags] // force react to rerender
    })
  }
  const saveTag = (tag: Tag): void => {
    // handle tags without text
    if (tag.text === '') {
      setTags(tags => [...tags, tag])
      setCurrentEntity(null)
      return;
    }
    setTags((tags) => {
      const index = tags.map(t => t.start_char).indexOf(tag.start_char)
      if (index < 0) return tags
      return [...tags.slice(0, index), tag, ...tags.slice(index + 1)]
    })
    setCurrentEntity(null)
    setRestoreState(null) // can't undo anymore
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
      if (!!tag.guid && !!tag.latitude && !!tag.longitude) return true
      return false
    }
    else { // tag is "NONE"
      return false
    }
  }

  const addNewTag = () => {
    const newTag: Tag = {
      text: '',
      type: "NONE",
      start_char: text.length,
      stop_char: text.length
    }
    setCurrentEntity(newTag)
  }

  const extendTagLeft = (): void => {
    const tag = currentEntity;
    if (!tag) return;
    // save state for easy undo
    if (!restoreState) {
      setRestoreState(tags)
    }
    const tagIndex = tags.map(tag => tag.start_char).indexOf(tag.start_char)
    if (tagIndex <= 0) return; // can't extend left
    const leftTag = tags[tagIndex - 1]
    const newTag: Tag = {
      ...tag,
      start_char: leftTag.start_char,
      stop_char: tag.stop_char,
      text: `${leftTag.text} ${tag.text}`,
      name: `${leftTag.text} ${tag.name}`,
    }
    setTags(tags => [...tags.slice(0, tagIndex - 1), newTag, ...tags.slice(tagIndex + 1)])
  }

  const extendTagRight = (): void => {
    const tag = currentEntity;
    if (!tag) return;
    // save state for easy undo
    if (!restoreState) {
      setRestoreState(tags)
    }
    const tagIndex = tags.map(tag => tag.start_char).indexOf(tag.start_char)
    if (tagIndex === tags.length) return; // can't extend right
    const rightTag = tags[tagIndex + 1]
    const newTag: Tag = {
      ...tag,
      start_char: tag.start_char,
      stop_char: rightTag.stop_char,
      text: `${tag.text} ${rightTag.text}`,
      name: `${tag.text} ${rightTag.text}`,
    }
    setTags(tags => [...tags.slice(0, tagIndex), newTag, ...tags.slice(tagIndex + 2)])
  }

  console.log({ tags })

  useEffect(() => {
    if (!data) return;
    const boundaries = data?.GetTextAnalysis.boundaries
    if (!boundaries) return;
    const people = data?.GetTextAnalysis.text_map.PERSON ?? []
    const places = data?.GetTextAnalysis.text_map.PLACE ?? []
    const times = data?.GetTextAnalysis.text_map.TIME ?? []
    const discoveredEntities: DiscoveredEntity[] = [
      ...people,
      ...places,
      ...times,
    ].sort((a, b) => a.start_char - b.start_char)
    setTags(boundaries.map((boundary) => {
      if (discoveredEntities.length && boundary.start_char === discoveredEntities[0].start_char) {
        const ent = discoveredEntities.shift()
        if (!ent || !ent.guids.length) return {
          // for now, only tag entities which already exist in the system
          start_char: boundary.start_char,
          stop_char: boundary.stop_char,
          text: boundary.text,
          type: "NONE"
        }
        if (ent.coords) return {
          start_char: ent.start_char,
          stop_char: ent.stop_char,
          text: ent.text,
          name: ent.text,
          guid: ent.guids[0],
          type: "PLACE",
          latitude: ent.coords[0].latitude,
          longitude: ent.coords[0].longitude
        }
        return {
          start_char: ent.start_char,
          stop_char: ent.stop_char,
          text: ent.text,
          name: ent.text,
          guid: ent.guids[0],
          type: people.includes(ent)
            ? "PERSON"
            :  "TIME"
        }
      }
      return {
        start_char: boundary.start_char,
        stop_char: boundary.stop_char,
        text: boundary.text,
        type: "NONE"
      }
    }))
  }, [data])
  if (loading) return <h1>loading...</h1> // replace with real loading screen app wide
  if (error) return <h1>Oops, there was an error: {error}</h1>
  return (
    <Box>
      <Grid 
        container
        spacing={2}
        direction='column'
        alignContent='center'
      >
        <Grid item xs={12} sm={6}>
          <Paper>
            <Typography align="center">Tag Citation</Typography>
            {
              tags.map(tag =>
                tag.type === "PERSON"
                  ? <Chip
                    label={tag.text ? tag.text : tag.name}
                    onDelete={() => clearTag(tag)}
                    onClick={() => setFocusedEntity(tag)}
                  />
                  : tag.type === "PLACE"
                    ? <Chip
                      label={tag.text ? tag.text : tag.name}
                      onDelete={() => clearTag(tag)}
                      onClick={() => setFocusedEntity(tag)}
                    />
                    : tag.type === "TIME"
                      ? <Chip
                        label={tag.text ? tag.text : tag.name}
                        onDelete={() => clearTag(tag)}
                        onClick={() => setFocusedEntity(tag)}
                      />
                      : <Chip
                        label={tag.text}
                        clickable
                        onClick={() => {
                          setCurrentEntity(tag)
                          setFocusedEntity(null)
                        }}
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
                  <Button onClick={extendTagLeft}>Extend tag left</Button>
                  <Button onClick={extendTagRight}>Extend tag right</Button>
                </FormControl>
                { // render sub component based on current radio value, as saved in currentEntity.type
                  currentEntity.type === "PERSON"
                    ? <TagPerson
                      currentEntity={currentEntity}
                      setCurrentEntity={setCurrentEntity}
                    />
                    : currentEntity.type === "PLACE"
                      ? <TagPlace currentEntity={currentEntity} setCurrentEntity={setCurrentEntity} />
                      : currentEntity.type === "TIME"
                        ? <TagTime text={currentEntity.text} setCurrentEntity={setCurrentEntity} />
                        : <br />
                }
                <br />

                <Button onClick={() => {
                  setCurrentEntity(null)
                  if (restoreState) {
                    setTags(restoreState)
                    setRestoreState(null)
                  }
                }}>Reset</Button>
                {canSaveTag(currentEntity) ?  // only show save button if complete
                  <Button
                    onClick={() => saveTag(currentEntity)}
                    disabled={!canSaveTag(currentEntity)}
                  >Save</Button>
                  : null
                }
              </>
              : focusedEntity ?
                <ViewEntity tag={focusedEntity} />
                :
                <>
                  <Typography align="center">Click a word to tag a Person, Place, or Time</Typography>
                  <Button
                    variant="contained"
                    onClick={addNewTag}
                  >Tag Entity without reference</Button>
                </>
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
