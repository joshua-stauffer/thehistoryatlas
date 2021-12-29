import { useState } from 'react';
import { Stepper, Step, StepLabel } from '@material-ui/core'

import { Source, AddSource } from './addSource'
import { Quote, AddQuote } from './addQuote'
import { Tag, TagEntities } from './tagEntities'


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
      child = <h1>add summary coming soon</h1>
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
