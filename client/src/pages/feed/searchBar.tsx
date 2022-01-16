import { useState } from 'react';
import { useQuery } from '@apollo/client';
import Autocomplete from '@mui/material/Autocomplete';
import { TextField } from '@mui/material'
import CircularProgress from '@mui/material/CircularProgress';

import { 
  GET_FUZZY_SEARCH_BY_NAME, 
  GetFuzzySearchByNameResult, 
  GetFuzzySearchByNameVars 
} from '../../graphql/getFuzzySearchByName';

interface SearchResult {
  name: string;
  guids: string[];
}  


interface SearchBarProps {

}


export const SearchBar = (props: SearchBarProps) => {
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [value, setValue] = useState<string | null>(null)

  const {
    data,
    loading,
    error
  } = useQuery<GetFuzzySearchByNameResult, GetFuzzySearchByNameVars>(
    GET_FUZZY_SEARCH_BY_NAME,
    { variables: { name: searchTerm } }
  )
  const options = data?.GetFuzzySearchByName ?? []

  return (
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
  )
}