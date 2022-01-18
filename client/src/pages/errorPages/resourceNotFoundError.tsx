import { Typography, Box, Paper } from '@mui/material'
import { NavBar, ExploreButton, SettingsButton, AddCitationButton, LoginButton } from '../../components/navBar'

export const ResourceNotFoundError = () => {
  return (
    <Box>
      <NavBar children={[
        <ExploreButton />,
        <AddCitationButton />,
        <LoginButton />,
        <SettingsButton />
      ]} />
      <Paper>
        <Typography variant="h1">Oops!</Typography>
        <Typography variant="h6">That page doesn't seem to exist.</Typography>
      </Paper>
    </Box>
  )
}