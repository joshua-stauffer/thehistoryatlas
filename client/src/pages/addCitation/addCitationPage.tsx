import { useState } from 'react';
import { Stepper, Step, StepLabel } from '@material-ui/core'

import { Source, AddSource } from './addSource'
import { Quote, AddQuote } from './addQuote'
import { Tag, TagEntities } from './tagEntities'
import { AddSummary } from './addSummary'

const mockSource: Source = {
  GUID: "143e08b2-8ed7-4289-894a-bad9d753cafd",
  author: "Nigel North",
  pubDate: undefined,
  publisher: "Indiana",
  title: "Bach: A History",
}

const mockQuote: Quote = {
  text: "Leopold, Prince of Anhalt-Köthen, hired Bach to serve as his Kapellmeister (director of music) in 1717."
}

const mockTags: Tag[] = [
  {
    guid: "ce433aaa-9a5a-4835-a41d-44480b9af079",
    name: "Leopold", 
    start_char: 0,
    stop_char: 7,
    text: "Leopold",
    type: "PERSON",
  },
  {
    guid: "d9a5a959-8948-47c7-8677-8cb227ea231d",
    latitude: 51.75185,
    longitude: 11.97093,
    name: "Köthen",
    start_char: 26,
    stop_char: 32,
    text: "Köthen",
    type: "PLACE",
  },
  {
    guid: "53ecef01-6391-4e6c-ba52-e8c09e8a4051",
    name: "1717",
    start_char: 98,
    stop_char: 102,
    text: "1717",
    type: "TIME",
  }
]

type CurrentStep = 0 | 1 | 2 | 3;

export const AddCitationPage = () => {
  const [source, setSource] = useState<Source>()
  const [quote, setQuote] = useState<Quote>()
  const [tags, setTags] = useState<Tag[]>()
  const [step, setStep] = useState<CurrentStep>(0)
  const addSource = (source: Source) => {
    setSource(source)
    setStep(1)
  }
  const addQuote = (quote: Quote) => {
    setQuote(quote)
    setStep(2)
  }
  const tagEntities = (tags: Tag[]) => {
    setTags(tags)
    setStep(3)
  }

  const steps = ["Add Source", "Add Quote", "Tag Entities", "Add Summary"]
  let child;
  switch (step) {

    case 0:
      child = <AddSource addSource={addSource} />
      break
    case 1:
      child = <AddQuote addQuote={addQuote} />
      break
    case 2:
      const text = quote ? quote.text : ''
      child = <TagEntities tagEntities={tagEntities} text={text} />
      break
    case 3:
      if (!tags || !quote || !source) {
        // type check for the compiler
        child = <h1>unexpected error</h1>; 
        break
      }
      child = <AddSummary tags={tags} quote={quote} source={source}/>
      break
  }
  return (
    <>
      <Stepper activeStep={step}>
        {steps.map((label, index) => (
          <Step key={index}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      {child}
    </>
  )
}
