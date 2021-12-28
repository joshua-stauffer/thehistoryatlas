import { useState } from 'react';
import { Stepper, Step, StepLabel } from '@material-ui/core'

import { Source, AddSource } from './addSource'
import { Quote, AddQuote } from './addQuote'


type Step = 0 | 1 | 2 | 3;

export const AddCitationPage = () => {
  const [ source, setSource ] = useState<Source>()
  const [ quote, setQuote ] = useState<Quote>()
  const [ step, setStep ] = useState<Step>(0)
  const addSource = (source: Source) => {
    setSource(source)
    setStep(1)
  }
  const addQuote = (quote: Quote) => {
    setQuote(quote)
    setStep(2)
  }

  const steps = ["Add Source", "Add Quote", "Tag Entities", "Add Summary"]
  let child;
  switch (step) {

    case 0:
      child = <AddSource addSource={addSource}/>
      break
    case 1:
      child = <AddQuote addQuote={addQuote} />
      break
    case 2:
      child = <h1>tag entities coming soon</h1>
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
