import { useState } from 'react'
import { makeStyles, Grid, TextField, Typography, Button } from '@material-ui/core'
import { colorTheme } from '../../baseStyle'


const useStyles = makeStyles(theme => ({
  container: {
    padding: theme.spacing(10),
    width: theme.spacing(38),
    border: theme.spacing(.2),
    borderStyle: 'solid',
    borderColor: colorTheme.dark.primary,
  },
  placeholder: {
    display: 'flex',
    alignItems: 'center',
    flexDirection: 'column',
    padding: theme.spacing(10),
  }
}));


export const SignUpPage = () => {

  const classes = useStyles();
  const [username, setUsername] = useState<string>('')
  const [password, setPassword] = useState<string>('')
  
  return (
    <Grid className={classes.placeholder}>
      <Grid className={classes.placeholder}></Grid>
      <Grid container className={classes.container}>
        <Grid item xs={12}>
          <Typography>
            The History Atlas
          </Typography>
        </Grid>
        <Grid item xs={12}>
          <TextField
            id="username"
            label="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            id="password"
            label="Reenter Password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
        </Grid>
        <Grid item alignItems="center">
          <Button variant="contained" onClick={() => console.log('submitted')}>
            Login
          </Button>
        </Grid>
      </Grid>
      <Grid className={classes.placeholder}></Grid>
    </Grid>
  )
}
