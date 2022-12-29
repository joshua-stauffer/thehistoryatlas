import { Typography, Box, Paper } from '@mui/material'
import { NavBar, ExploreButton, SettingsButton, AddCitationButton, LoginButton } from '../../components/navBar'
import { TokenManager } from '../../hooks/token'

interface ResourceNotFoundErrorProps {
  tokenManager: TokenManager
}

export const ResourceNotFoundError = (props: ResourceNotFoundErrorProps) => {
  return (
    <Box>
      <NavBar children={[
        <ExploreButton />,
        <AddCitationButton />,
        <LoginButton tokenManager={props.tokenManager}/>,
        <SettingsButton />
      ]} />
      <Paper>
        <Typography variant="h1">Oops!</Typography>
        <Typography variant="h6">That page doesn't seem to exist.</Typography>
      </Paper>
    </Box>
  )
}