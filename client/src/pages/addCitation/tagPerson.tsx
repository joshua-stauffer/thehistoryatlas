import { useState } from 'react'
import { useQuery } from '@apollo/client'
import { Box, Button, List, ListItem, Paper, TextField, Typography } from '@material-ui/core'
import Skeleton from '@mui/material/Skeleton';
import Divider from '@mui/material/Divider';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import { Tag } from './tagEntities'
import { GET_GUIDS_BY_NAME, GUIDsByNameResult, GUIDsByNameVars } from '../../graphql/getGUIDsByName'
import { v4 } from 'uuid';

interface TagPersonProps {
  currentEntity: Tag | null
  setCurrentEntity: React.Dispatch<React.SetStateAction<Tag | null>>
}


export const TagPerson = (props: TagPersonProps) => {
  const { currentEntity, setCurrentEntity } = props;
  const [personTagName, setPersonTagName] = useState<string>(currentEntity?.text ?? '')
  const [newPersonGUID] = useState<string>("new-" + v4())
  const [showSearchResults, setShowSearchResults] = useState<boolean>(false)
  const {
    data, loading, error
  } = useQuery<GUIDsByNameResult, GUIDsByNameVars>(GET_GUIDS_BY_NAME,
    { variables: { name: personTagName } }
  )
  const results = data?.GetGUIDsByName.summaries.filter(entity => entity.type === "PERSON") ?? []
  results.push({
    type: "PERSON",
    guid: newPersonGUID,
    citation_count: 0,
    names: [personTagName],
    first_citation_date: "This is a new entity",
    last_citation_date: "and doesn't have any citations yet."
  })
  console.log({currentEntity})

  const searchBar = (
      <Paper>
        <TextField
          variant="outlined"
          label="Search for Person" 
          defaultValue={personTagName} 
          onChange={(event) => setPersonTagName(event.target.value)} 
        />
        <Button onClick={() => {
          setShowSearchResults(true)
          setCurrentEntity(entity => {
            return {
              ...entity,
              name: personTagName
            } as Tag
          })
        }}
      >Search</Button>
      </Paper>
  )

  const searchResults = (
    <>
    <Typography>Tag a Person:</Typography>
          <List>
            <Button onClick={() => {
              setShowSearchResults(false)
            }
            }>Start Over</Button>
            {loading ?
              <Skeleton variant="rectangular" width={210} height={118} />
              : currentEntity?.name ? results.map(entity =>
                <ListItem>
                  <ListItemButton
                    selected={currentEntity.guid === entity.guid}
                    onClick={() => {
                      let updatedGUID: string | null;
                      if (currentEntity.guid === entity.guid) {
                        // if this entity is already selected, de-select it
                        updatedGUID = null
                      } else {
                        // otherwise, select it
                        updatedGUID = entity.guid
                      }
                      setCurrentEntity(ent => {
                        return {
                          ...ent,
                          guid: updatedGUID
                        } as Tag
                      })
                    }
                    }
                    align-items="flex-start"
                  >
                    {
                      entity.guid === newPersonGUID
                        ?
                        <>
                          <Divider />
                          <Paper>
                            <Typography>Create new entity from name: {entity.names}</Typography>
                          </Paper>
                        </>
                        : // otherwise, add a typical list item
                        <Paper>
                          <ListItemText>Names: {entity.names}</ListItemText> <br />
                          <ListItemText>Appears in {entity.citation_count} Citations</ListItemText><br />
                          <ListItemText>Date of earliest citation: {entity.first_citation_date}</ListItemText><br />
                          <ListItemText>Date of latest citation: {entity.last_citation_date}</ListItemText>
                        </Paper>
                    }
                  </ListItemButton>
                </ListItem>
              )
                : <ListItem><ListItemText>Please search for person by name</ListItemText></ListItem>
            }
          </List>
      </>
  )


  return (
    <Box>
      <Paper>
        {
          showSearchResults 
            ? searchResults
            : searchBar
        }
          
      </Paper>
    </Box>
  )
}