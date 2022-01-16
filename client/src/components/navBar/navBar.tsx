import { AppBar, Toolbar, Typography } from '@mui/material'

interface NavBarProps {
  children: JSX.Element[]
}


export const NavBar = (props: NavBarProps) => {
  const { children } = props;
  // TODO: add spacer
  return (
    <>
    <AppBar position="fixed">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          The History Atlas
        </Typography>
        { children }
      </Toolbar>
    </AppBar>
  
    </>
  )
}