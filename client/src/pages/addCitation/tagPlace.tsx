import { Tag } from './tagEntities'
import { useState } from 'react'
import { useQuery } from '@apollo/client'
import { Box, Button, Paper, TextField, Typography } from '@material-ui/core'
import { GET_COORDINATES_BY_NAME, CoordinatesByNameResult, CoordinatesByNameVars } from '../../graphql/getCoordinatesByName'
import { GET_PLACE_BY_COORDS, GetPlaceByCoordsResult, GetPlaceByCoordsVars } from '../../graphql/getPlaceByCoords'
import { SingleEntityMap } from '../../components/singleEntityMap';
import { v4 } from 'uuid';
import { useEffect } from 'react';


interface TagPlaceProps {
  currentEntity: Tag | null
  setCurrentEntity: React.Dispatch<React.SetStateAction<Tag | null>>
  placeName: string
}

interface TagPlaceWrapperProps {
  currentEntity: Tag | null
  setCurrentEntity: React.Dispatch<React.SetStateAction<Tag | null>>
}

export const TagPlace = (props: TagPlaceWrapperProps) => {
  const { currentEntity, setCurrentEntity } = props;
  const [placeName, setPlaceName] = useState<string>(currentEntity?.text ?? '')
  const [showSearchResults, setShowSearchResults] = useState<boolean>(false)
  // this component delays network calls until the user has clicked 'search'
  if (!showSearchResults) {
    return (
      <>
        <TextField
          variant="outlined"
          defaultValue={placeName}
          label="Search for place by name"
          onChange={(event) => setPlaceName(event.target.value)}
        />
        <Button onClick={() => {
          setCurrentEntity(entity => {
            return {
              ...entity,
              name: placeName
            } as Tag
          })
          setShowSearchResults(true)
        }
        }>Search</Button>
      </>
    )
  } else {
    return <TagPlaceHelper currentEntity={currentEntity} setCurrentEntity={setCurrentEntity} placeName={placeName} />
  }
}


export const TagPlaceHelper = (props: TagPlaceProps) => {
  const { currentEntity, setCurrentEntity, placeName } = props;
  const [newPlaceGUID] = useState<string>(v4())
  const [latitude, setLatitude] = useState<number>(0)
  const [searchIndex, setSearchIndex] = useState<number>(0)

  const updateLatitude = (latitude: string): void => {
    if (latitude === '') {
      setLatitude(0)
    }
    const num = Number.parseFloat(latitude)
    if (!Number.isNaN(num) && num >= -90 && num <= 90) {
      setLatitude(Number.parseFloat(latitude))
    }
  }
  const [longitude, setLongitude] = useState<number>(0)
  const updateLongitude = (longitude: string): void => {
    if (longitude === '') {
      setLongitude(0)
    }
    const num = Number.parseFloat(longitude)
    if (!Number.isNaN(num) && num >= -180 && num <= 180) {
      setLongitude(Number.parseFloat(longitude))
    }
  }

  // look up coordinates for the text provided by user
  const {
    data: coordinatesByNameData,
    loading: coordinatesByNameLoading,
    error: coordinatesByNameError
  } = useQuery<CoordinatesByNameResult, CoordinatesByNameVars>(
    GET_COORDINATES_BY_NAME, {
    variables: { name: currentEntity?.name ?? "" }
  })

  const results = coordinatesByNameData?.GetCoordinatesByName ?? []

  useEffect(() => {
    if (!!results.length && searchIndex < results.length) {
      setCurrentEntity(entity => {
        if (!entity) return entity
        return {
          ...entity,
          latitude: results[searchIndex].latitude,
          longitude: results[searchIndex].longitude,
          guid: newPlaceGUID  // require new backend logic to resolve existing GUIDs
        }
      })
    } else if (searchIndex === results.length) {
      setCurrentEntity(entity => {
        if (!entity) return entity
        return {
          ...entity,
          latitude: latitude,
          longitude: longitude,
          guid: newPlaceGUID
        }
      })
    }
  }, [searchIndex, latitude, longitude, results, newPlaceGUID, setCurrentEntity])

  // given coordinates, look up if the current chosen place exists in the DB
  const {
    data: placeByCoordsData,
    loading: placeByCoordsLoading,
    error: placeByCoordsError
  } = useQuery<GetPlaceByCoordsResult, GetPlaceByCoordsVars>(
    GET_PLACE_BY_COORDS, {
    variables: { 
      latitude: currentEntity?.latitude ? currentEntity.latitude : latitude,
      longitude: currentEntity?.longitude ? currentEntity.longitude : longitude,
     }
  })
  // keep currentEntity GUID in sync
  useEffect(() => {
    if (!placeByCoordsData) return;
    setCurrentEntity(entity => {
      if (!entity) return entity;
      const guid = placeByCoordsData.GetPlaceByCoords.guid ? placeByCoordsData.GetPlaceByCoords.guid : newPlaceGUID
      return {
        ...entity,
        guid: guid
      }
    })
  })


  const getSearchResult = () => {
    if (!!results.length && searchIndex < results.length) {
      // we can safely index into the results array
      return (
        <Paper>
          <Typography>
            <Button
              variant="contained"
              disabled={searchIndex === 0}
              onClick={() => setSearchIndex(index => index - 1)}
            >Previous</Button>
            {searchIndex + 1} of {results.length}
            <Button
              variant="contained"
              disabled={searchIndex === results.length}
              onClick={() => setSearchIndex(index => index + 1)}
            >{searchIndex < results.length - 1 ? "Next" : "Add Custom Coordinates"}</Button></Typography>
          <SingleEntityMap
            latitude={results[searchIndex].latitude}
            longitude={results[searchIndex].longitude}
            zoom={5}
            title={placeName}
            mapTyle={"basic"}
            size={"XS"}
          />
        </Paper>
      )
    } else {
      // give the user an option to add a new place
      return (
        <Paper>
          <Typography>Add a New Place</Typography>
          <Button
            variant="contained"
            disabled={searchIndex === 0}
            onClick={() => setSearchIndex(index => index - 1)}
          >Previous</Button>
          <TextField
            id="latitude"
            label="Latitude"
            type="number"
            value={latitude}
            InputLabelProps={{
              shrink: true,
            }}
            variant="standard"
            onChange={(event) => updateLatitude(event.currentTarget.value)}
          />
          <TextField
            id="longitude"
            label="Longitude"
            type="number"
            value={longitude}
            InputLabelProps={{
              shrink: true,
            }}
            variant="standard"
            onChange={(event) => updateLongitude(event.currentTarget.value)}
          />
          <SingleEntityMap
            latitude={latitude}
            longitude={longitude}
            zoom={5}
            title={placeName}
            mapTyle={"basic"}
            size={"XS"}
          />
        </Paper>
      )
    }
  }
  return (
    <Box>
      <Paper>

        {
          placeByCoordsLoading || coordinatesByNameLoading 
          ?
          <Typography variant="h2">Loading...</Typography>
          :
          getSearchResult()
        }
      </Paper>
    </Box>
  )
}
