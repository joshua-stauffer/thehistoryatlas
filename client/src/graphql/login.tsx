import { gql } from "@apollo/client";

export const LOGIN = gql`
  mutation Login($username: String!, $password: String!) {
    Login(username: $username, password: $password) {
      success
      token
    }
  }
`;

export interface LoginResult {
  Login: {
    success: boolean;
    token: string;
  };
}

export interface LoginVars {
  username: string;
  password: string;
}
