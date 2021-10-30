import { ApolloError } from '@apollo/client';
import { GetTextAnalysisResult } from '../../graphql/getTextAnalysis';
import { Panel, PanelContainer  } from './style';
import { Loading } from './loading';
import { ControlBar } from './controlBar';
import { TextAndMeta } from './annotatePage';


interface TagTextProps {
  processedText: GetTextAnalysisResult | undefined;
  textIsLoading: boolean;
  textError: ApolloError | undefined;
  submitFunc: () => void;
  backFunc: () => void;
}

export const TagText = (props: TagTextProps) => {
  const { 
    processedText,
    textIsLoading, 
    textError, 
    submitFunc, 
    backFunc 
  } = props;

  console.log('processed text is ', processedText)
  if (textIsLoading) {
    return <Loading />
  }
  return (
    <>
    <PanelContainer>
      <Panel>

      </Panel>
      <Panel>

      </Panel>
    </PanelContainer>
    <ControlBar
      title={''}
      forwardFunc={submitFunc}
      disableForward={ false }
      backFunc={backFunc}
      disableBack={false}
    />
  </>

  )
}