import { Button } from '@mui/material'
import { Link } from 'react-router-dom'


export const ExploreButton = () => {
  return (
    <Link to="/">
      <Button color="inherit">Explore</Button>
    </Link>
  )
}