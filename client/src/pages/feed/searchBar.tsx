import { useState } from 'react';
import { useQuery } from '@apollo/client';
import Autocomplete from '@mui/material/Autocomplete';
import { TextField, Button, Typography } from '@mui/material'
import CircularProgress from '@mui/material/CircularProgress';

import { addToHistoryProps } from '../../hooks/history'
import { 
  GET_FUZZY_SEARCH_BY_NAME, 
  GetFuzzySearchByNameResult, 
  GetFuzzySearchByNameVars 
} from '../../graphql/getFuzzySearchByName';

import {
  GET_ENTITY_SUMMARIES_BY_GUID,
  GetEntitySummariesByGUIDResult,
  GetEntitySummariesByGUIDVars
} from '../../graphql/getEntitySummariesByGUID'

interface SearchResult {
  name: string;
  guids: string[];
}  


interface SearchBarProps {
  setCurrentEntity: (props: addToHistoryProps) => void
}


export const SearchBar = (props: SearchBarProps) => {
  const { setCurrentEntity } = props;
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [value, setValue] = useState<string | null>(null)

  const {
    data: getFuzzySearchByNameData,
    loading,
    error
  } = useQuery<GetFuzzySearchByNameResult, GetFuzzySearchByNameVars>(
    GET_FUZZY_SEARCH_BY_NAME,
    { variables: { name: searchTerm } }
  )
  const options = getFuzzySearchByNameData?.GetFuzzySearchByName ?? []


  const getGUIDs = (): string[] => {
    if (!options.length) return ['']
    const option = options.find(opt => opt.name === value)
    if (!option) return ['']
    return option.guids
  }

  const {
    data: entitySummaryByGUIDData,
    error: entitySummaryByGUIDError,
    loading: entitySummaryByGUIDLoading
  } = useQuery<GetEntitySummariesByGUIDResult, GetEntitySummariesByGUIDVars>(
    GET_ENTITY_SUMMARIES_BY_GUID,
    { variables: { guids: getGUIDs() }}
  )

  const handleSearch = () => {
    if (!value || !entitySummaryByGUIDData 
      || !entitySummaryByGUIDData.GetEntitySummariesByGUID.length) return;
    // taking the first summary
    const summary = entitySummaryByGUIDData.GetEntitySummariesByGUID[0]
    setCurrentEntity({
      entity: {
        guid: summary.guid,
        type: summary.type,
        name: summary.names[0]
      }
    })
  }


  return (
    <>
    <Autocomplete
      sx={{ minWidth: 300 }}
      options={options.map((option) => option.name)}
      loading={loading}
      disablePortal
      value={value}
      onChange={(_, newValue) => {
        setValue(newValue);
      }}
      inputValue={searchTerm}
      onInputChange={(_, newInputValue) => setSearchTerm(newInputValue)}
      renderInput={(params) => (
        <TextField
           {...params} 
           label="Search for an entity" 
           fullWidth 
           InputProps={{
            ...params.InputProps,
            endAdornment: (
              <>
                {loading ? <CircularProgress color="inherit" size={20} /> : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}

    />
    <Button onClick={handleSearch}><Typography>Search</Typography></Button>
    </>
  )
}