import Button from "@mui/material/Button";
import { useHistory } from "react-router-dom";
import { TokenManager } from "../../hooks/token";

interface LoginButtonProps {
  tokenManager: TokenManager;
}

export const LoginButton = (props: LoginButtonProps) => {
  const {
    tokenManager: { isLoggedIn, logout },
  } = props;
  const history = useHistory();
  if (isLoggedIn()) {
    return (
      <Button color="secondary" onClick={logout}>
        Logout
      </Button>
    );
  }
  return (
    <Button color="secondary" onClick={() => history.push("/login")}>
      Login
    </Button>
  );
};
