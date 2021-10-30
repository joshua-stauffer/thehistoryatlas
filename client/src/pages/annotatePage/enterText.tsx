import { useState } from 'react';
import { TextBox, Panel, PanelContainer, Input  } from './style';
import { ControlBar } from './controlBar';

interface EnterTextProps {
  submitFunc: (submitProps: SubmitFuncProps) => void;
}

export interface SubmitFuncProps {
  citationText: string;
  title: string;
  author: string;
  publisher: string;
  pageNumber: string;
  url: string;
}

export const EnterText = ({ submitFunc }: EnterTextProps) => {
  const [ citationText, setCitationText ] = useState<string>('')
  const [ title, setTitle ] = useState<string>('')
  const [ author, setAuthor ] = useState<string>('')
  const [ publisher, setPublisher ]= useState<string>('')
  const [ pageNumber, setPageNumber ] = useState<string>('')
  const [ url, setUrl ] = useState<string>('')
  const submitProps = {
    citationText: citationText,
    title: title,
    author: author,
    publisher: publisher,
    pageNumber: pageNumber,
    url: url
  }



  const canSubmit: boolean =
    citationText.length > 0
    && title.length > 0
    && author.length > 0
    && publisher.length > 0;

  return (
    <>
      <PanelContainer>
        <Panel>
          <label>
            <p>Title</p>
            <Input onChange={e => setTitle(e.target.value)}></Input>
          </label>
          <label>
            <p>Author/s</p>
            <Input onChange={e => setAuthor(e.target.value)}></Input>
          </label>
          <label>
            <p>Publisher</p>
            <Input onChange={e => setPublisher(e.target.value)}></Input>
          </label>
          <label>
            <p>Page Number (optional)</p>
            <Input onChange={e => setPageNumber(e.target.value)}></Input>
          </label>        
          <label>
            <p>URL (optional)</p>
            <Input onChange={e => setUrl(e.target.value)}></Input>
          </label>
        </Panel>
        <Panel>
          <h2>Citation Text</h2>
          <TextBox required onChange={e => setCitationText(e.target.value)} />

        </Panel>
      </PanelContainer>
      <ControlBar
        title={''}
        forwardFunc={() => submitFunc(submitProps)}
        disableForward={ !canSubmit }
        backFunc={() => console.log('back')}
        disableBack={true}
      />
    </>
  )
}