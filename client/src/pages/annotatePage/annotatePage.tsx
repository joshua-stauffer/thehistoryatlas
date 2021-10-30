import { useState } from 'react';
import { useQuery } from '@apollo/client';
import { GET_TEXT_ANALYSIS, GetTextAnalysisResult, GetTextAnalysisVars } from '../../graphql/getTextAnalysis';
import { Container, TextBox, Panel, PanelContainer,  } from './style';
import { EnterText, SubmitFuncProps } from './enterText';
import { TagText } from './tagText';
import { ConfirmTags } from './confirmTags';

type AnnotateStage = 1 | 2 | 3;

export interface TextAndMeta {
  text: string;
  meta: {
    author: string;
    title: string;
    publisher: string;
    pageNumber?: string;
    url?: string;
  }
}

export const AnnotatePage = () => {
  const [stage, setStage] = useState<AnnotateStage>(1)

  // stage 1 
  const [textAndMeta, setTextAndMeta]= useState<TextAndMeta | null>(null)
  const completeStepOne = (props: SubmitFuncProps) => {
    const { citationText, title, author, publisher, pageNumber, url } = props;
    setTextAndMeta({
      text: citationText,
      meta: {
        title: title,
        author: author,
        publisher: publisher,
        pageNumber: pageNumber,
        url: url
      }
    })
    setStage(2)
  }
  // stage 2
  const returnToStageOne = () => {
    setStage(1)
  }
  const {
    loading: textLoading, 
    error: textError, 
    data: textData 
  } = useQuery<GetTextAnalysisResult, GetTextAnalysisVars>(
    GET_TEXT_ANALYSIS,
    { variables: { text: textAndMeta && textAndMeta.text ? textAndMeta.text : ''} }
  )
  
  if (stage === 1) {
    return (
      <Container>
        <EnterText
          submitFunc={completeStepOne}
        />
      </Container>
    ) 
  } else if (stage === 2) {
    return (
      <Container>
        <TagText
          processedText={textData}
          textIsLoading={textLoading}
          textError={textError}
          backFunc={returnToStageOne}
          submitFunc={() => null}
        />
      </Container>
    ) 
  } else if (stage === 3) {
    return (
      <Container>
        
      </Container>
    ) 
  }
  else throw new Error('Expected stage to be 1, 2, or 3')
}