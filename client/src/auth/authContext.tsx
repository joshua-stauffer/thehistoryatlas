import React, { createContext, useCallback, useContext, useState } from "react";

interface AuthState {
  token: string | null;
  username: string | null;
}

interface AuthContextValue extends AuthState {
  setAuth: (token: string, username: string) => void;
  logout: () => void;
  isLoggedIn: boolean;
}

const TOKEN_KEY = "tha_token";
const USERNAME_KEY = "tha_username";

const AuthContext = createContext<AuthContextValue>({
  token: null,
  username: null,
  isLoggedIn: false,
  setAuth: () => {},
  logout: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [auth, setAuthState] = useState<AuthState>(() => ({
    token: localStorage.getItem(TOKEN_KEY),
    username: localStorage.getItem(USERNAME_KEY),
  }));

  const setAuth = useCallback((token: string, username: string) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USERNAME_KEY, username);
    setAuthState({ token, username });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USERNAME_KEY);
    setAuthState({ token: null, username: null });
  }, []);

  return (
    <AuthContext.Provider
      value={{
        ...auth,
        isLoggedIn: auth.token !== null,
        setAuth,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
