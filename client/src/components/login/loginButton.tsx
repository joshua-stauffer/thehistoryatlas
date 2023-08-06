import Button from "@mui/material/Button";
import { useNavigate } from "react-router-dom";
import { TokenManager, useTokenManager } from "../../hooks/token";
import { useState } from "react";
import LoginDialog from "./loginDialog";

interface LoginButtonProps {}

export const LoginButton = (props: LoginButtonProps) => {
  const [open, setOpen] = useState<boolean>(false);
  const { isLoggedIn, logout } = useTokenManager();
  if (open) {
    return <LoginDialog open={open} setOpen={setOpen} />;
  }
  if (isLoggedIn()) {
    return (
      <Button color="secondary" onClick={logout}>
        Logout
      </Button>
    );
  }
  return (
    <Button color="secondary" onClick={() => setOpen(true)}>
      Login
    </Button>
  );
};
