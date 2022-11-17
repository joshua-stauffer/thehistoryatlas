import { makeVar } from '@apollo/client';

export interface LoginResponse {
  success: boolean;
  token?: string;
}

type Token = string | null;

const tokenVar = makeVar<Token>(null)

export const login = (loginResponse: LoginResponse): void => {
  const { token, success } = loginResponse;
  if (success) {
    tokenVar(token)
  }
  else {
    tokenVar(null)
  }
}

export const logout = () => {
  tokenVar(null)
}

export const getToken = (): Token => {
  return tokenVar()
}

export const isLoggedIn = (): boolean => {
  return !!tokenVar()
}