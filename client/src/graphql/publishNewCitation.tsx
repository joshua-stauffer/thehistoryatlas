import { gql } from "@apollo/client";

export const PUBLISH_NEW_CITATION = gql`
  mutation PublishNewCitation($Annotation: AnnotateCitationInput!) {
    PublishNewCitation(Annotation: $Annotation) {
      code
      success
      message
    }
  }
`

export interface PublishNewCitationResult {
  code: string
  success: boolean
  message: string
}

export interface PublishNewCitationVars {
  Annotation: {
    citation_guid: string
    citation: string
    summary_guid: string
    summary: string
    summary_tags: {
      type: "PERSON" | "PLACE" | "TIME"
      start_char: number
      stop_char: number
      GUID: string
      name: string
      latitude?: number
      longitude?: number
      geoshape?: string
    }[]
    meta: {
      title: string
      author: string
      publisher: string
      pubDate?: string
      pageNum?: number
      GUID: string
    }
  }
}
