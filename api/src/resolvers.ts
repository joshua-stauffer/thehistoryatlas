// Resolver for the History Atlas Apollo GraphQL API

import { Context } from './index';
import { Resolver, WriteModelResponse, Accounts } from './types'

const APP_VERSION = '0.1.0'

type ResolverFn = (parent: any, args: any, ctx: any) => any;
interface ResolverMap {
  [field: string]: ResolverFn;
}
interface Resolvers {
  Query: ResolverMap;
  Mutation: ResolverMap;
}

export const resolvers: Resolvers = {
  Query: {

    GetSummariesByGUID: async (_,
      { summary_guids }: Resolver.GetSummariesByGUIDsArgs,
      { queryReadModel }: Context) => {
      const msg = {
        type: "GET_SUMMARIES_BY_GUID",
        payload: {
          summary_guids: summary_guids
        }
      }
      try {
        console.debug(`Publishing query`, msg)
        const { payload } = await queryReadModel(msg) as Resolver.SummariesByGUID;
        console.debug('received result: ', payload)
        return payload.summaries
      } catch (err) {
        return {
          code: 'Error',
          success: false,
          message: err
        }
      }
    },
    
    GetCitationByGUID: async (_,
      { citationGUID }: Resolver.GetCitationByGUIDsArgs,
      { queryReadModel }: Context) => {
        const msg = {
          type: "GET_CITATION_BY_GUID",
          payload: {
            citation_guid: citationGUID
          }
        }
        try {
          console.debug(`Publishing query`, msg)
          const { payload } = await queryReadModel(msg) as Resolver.CitationByGUID;
          console.debug('received result: ', payload)
          return payload.citation
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err
          }
        }
    },
    GetManifest: async (_,
      { entityType, GUID }: Resolver.GetManifestArgs,
      { queryReadModel }: Context) => {
      const msg = {
        type: "GET_MANIFEST",
        payload: {
          type: entityType,
          guid: GUID
        }
      }
      try {
        console.debug(`Publishing query `, msg)
        console.debug(msg.payload)

        const { payload } = await queryReadModel(msg) as Resolver.Manifest;
        console.debug('received result: ', payload)
        return {
          guid: payload.guid,
          citation_guids: payload.citation_guids,
          timeline: payload.timeline
        }
      } catch (err) {
        return {
          code: 'Error',
          success: false,
          message: err
        }
      }
    },
    GetGUIDsByName: async (_,
      { name }: Resolver.GetGUIDsByNameArgs,
      { queryReadModel }: Context) => {
      const msg = {
        type: "GET_GUIDS_BY_NAME",
        payload: {
          name: name,
        }
      }
      try {
        console.debug(`Publishing query ${msg}`)
        const { payload } = await queryReadModel(msg) as Resolver.GUIDByName;
        console.debug('received result: ', payload)
        console.debug('payload.guids is ', payload.guids)
        return payload
      } catch (err) {
        return {
          code: 'Error',
          success: false,
          message: err
        }
      }
    },
    GetCoordinatesByName: async (_,
      { name }: Resolver.GetCoordinatesByNameArgs,
      { queryGeo }: Context) => {
      const msg = {
        type: "GET_COORDS_BY_NAME",
        payload: {
          "name": name
        }
      }
      try {
        console.debug(`Publishing query `, msg)
        console.debug(msg.payload)

        const { payload } = await queryGeo(msg) as Resolver.CoordsByName;
        console.debug('received result: ', payload);
        const geoResult = payload.coords[name];
        if (!geoResult) throw new Error(`GeoService returned unknown result: ${geoResult}`);
        return geoResult
      } catch (err) {
        return {
          code: 'Error',
          success: false,
          message: err
        }
      }
    },

    GetTextAnalysis: async (_,
      { text }: Resolver.GetTextAnalysisArgs,
      { queryNLP }: Context) => {
      const msg = {
        type: "PROCESS_TEXT",
        payload: {
          text: text
        }
      }
      try {
        console.debug(`Publishing query `, msg)
        console.debug(msg.payload)

        const { payload } = await queryNLP(msg) as Resolver.TextProcessed;
        console.debug('received result: ', payload);
        return payload
      } catch (err) {
        return {
          code: 'Error',
          success: false,
          message: err
        }
      }
    },

    // ACCOUNTS MESSAGES

    GetUser: async (_,
      { token }: Accounts.GetUserPayload,
      { queryAccounts }: Context) => {
        const msg: Accounts.GetUserQuery = {
          type: "GET_USER",
          payload: {
            token: token
          }
        }
        try {
          console.debug('Publishing query ', msg)
          console.debug(msg.payload)

          const { payload } = await queryAccounts(msg) as Accounts.GetUserResult;
          console.debug('received result: ', payload)
          return payload
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err
          }
        }
      },

      IsUsernameUnique: async (_,
        { username }: Accounts.IsUsernameUniquePayload,
        { queryAccounts }: Context) => {
          const msg: Accounts.IsUsernameUniqueQuery = {
            type: "IS_USERNAME_UNIQUE",
            payload: {
              username: username
            }
          }
          try {
            console.debug('Publishing query ', msg)
            console.debug(msg.payload)
  
            const { payload } = await queryAccounts(msg) as Accounts.IsUsernameUniqueResult;
            console.debug('received result: ', payload)
            return payload
          } catch (err) {
            return {
              code: 'Error',
              success: false,
              message: err
            }
          }
        },

              

  }, // end of Query

  Mutation: {

    PublishNewCitation: async (_,
      { Annotation }: Resolver.PublishNewCitationArgs,
      { emitCommand }: Context) => {
        console.debug('Publishing the following command: ', Annotation)
        const payload = Annotation;
        try {
          const result = await emitCommand({
            type: 'PUBLISH_NEW_CITATION',
            app_version: APP_VERSION,
            timestamp: new Date().toJSON(),
            // TODO: update this to reflect the current user
            user: 'test-user',
            payload: payload
          }) as WriteModelResponse;
          console.debug('received result from emitting command ', result)
          if (result.type === 'COMMAND_FAILED') {
            let message: string;
            if (result.payload) {
              message = 'Your Citation has not been processed due to an error: ' + result.payload.reason
            } else {
              message = 'Your Citation has not been processed due to an error.'
            }
            return {
              code: 'Failure',
              success: false,
              message: message
            }
          }
          return {
            code: 'Success',
            success: true,
            message: 'Your Citation has been processed'
          }
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err // this may run the risk of exposing sensitive data -- debug only
        }
      }
    },

    AddUser: async (_,
      { token, user_details }: Accounts.AddUserPayload,
      { queryAccounts }: Context) => {
        const msg: Accounts.AddUserQuery = {
          type: "ADD_USER",
          payload: {
            token: token,
            user_details: user_details
          }
        }
        try {``
          console.debug('Publishing query ', msg)
          console.debug(msg.payload)

          const { payload } = await queryAccounts(msg) as Accounts.AddUserResult;
          console.debug('received result: ', payload)
          return payload
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err
          }
        }
      },

    UpdateUser: async (_,
      { token, user_details }: Accounts.UpdateUserPayload,
      { queryAccounts }: Context) => {
        const msg: Accounts.UpdateUserQuery = {
          type: "UPDATE_USER",
          payload: {
            token: token,
            user_details: user_details
          }
        }
        try {
          console.debug('Publishing query ', msg)
          console.debug(msg.payload)

          const { payload } = await queryAccounts(msg) as Accounts.UpdateUserResponse;
          console.debug('received result: ', payload)
          return payload
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err
          }
        }
      },

    Login: async (_,
      { username, password }: Accounts.LoginPayload,
      { queryAccounts }: Context) => {
        const msg: Accounts.LoginQuery = {
          type: "LOGIN",
          payload: {
            username: username,
            password: password
          }
        }
        try {
          console.debug('Publishing query ', msg)
          console.debug(msg.payload)

          const { payload } = await queryAccounts(msg) as Accounts.LoginResult;
          console.debug('received result: ', payload)
          return payload
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err
          }
        }
      },

    DeactivateAccount: async (_,
      { token, username }: Accounts.DeactivateAccountPayload,
      { queryAccounts }: Context) => {
        const msg: Accounts.DeactivateAccountQuery = {
          type: "DEACTIVATE_ACCOUNT",
          payload: {
            token: token,     // admin token required
            username: username  // user to be deactivated
          }
        }
        try {
          console.debug('Publishing query ', msg)
          console.debug(msg.payload)

          const { payload } = await queryAccounts(msg) as Accounts.DeactivateAccountResult;
          console.debug('received result: ', payload)
          return payload
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err
          }
        }
      },

    ConfirmAccount: async (_,
      { token }: Accounts.ConfirmAccountPayload,
      { queryAccounts }: Context) => {
        const msg: Accounts.ConfirmAccountQuery = {
          type: "CONFIRM_ACCOUNT",
          payload: {
            token: token
          }
        }
        try {
          console.debug('Publishing query ', msg)
          console.debug(msg.payload)

          const { payload } = await queryAccounts(msg) as Accounts.ConfirmAccountResult;
          console.debug('received result: ', payload)
          return payload
        } catch (err) {
          return {
            code: 'Error',
            success: false,
            message: err
          }
        }
      },
  }
} // end of Resolvers
