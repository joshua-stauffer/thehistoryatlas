import { gql } from "@apollo/client";

export const PUBLISH_NEW_CITATION = gql`
  mutation PublishNewCitation($Annotation: AnnotateCitationInput!) {
    PublishNewCitation(Annotation: $Annotation) {
      success
      message
    }
  }
`

export interface PublishNewCitationResult {
  success: boolean
  message: string
}

export interface PublishNewCitationVars {
  Annotation: {
    citationId: string
    citation: string
    summaryId?: string
    summary: string
    summaryTags: {
      type: "PERSON" | "PLACE" | "TIME"
      startChar: number
      stopChar: number
      id?: string
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
      id?: string
    }
    token: string
  }
}
