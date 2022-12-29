import { useState } from 'react';
import Stepper from '@mui/material/Stepper'
import Step from '@mui/material/Step'
import StepLabel from '@mui/material/StepLabel'
import Box from '@mui/material/Box';
import { v4 } from 'uuid';
import { theme } from '../../baseStyle'

import { ExploreButton, SettingsButton } from '../../components/navBar';
import { PublishNewCitationVars } from '../../graphql/publishNewCitation';
import { Source, AddSource } from './addSource'
import { Quote, AddQuote } from './addQuote'
import { Tag, TagEntities } from './tagEntities'
import { Summary, AddSummary } from './addSummary'
import { SaveSummary } from './saveAnnotatedCitation';
import { NavBar } from '../../components/navBar';
import { useToken } from '../../hooks/token';
import { useHistory } from 'react-router-dom';



type CurrentStep = 0 | 1 | 2 | 3 | 4;

export const AddCitationPage = () => {
  const history = useHistory()
  const { token } = useToken()
  const [citationGUID, ] = useState<string>(v4())  // allows api to reject duplicate requests
  const [summaryGUID, ] = useState<string | undefined>(undefined)  // for now, can't tag an existing summary
  const [source, setSource] = useState<Source>()
  const [quote, setQuote] = useState<Quote>()
  const [tags, setTags] = useState<Tag[]>()
  const [summary, setSummary] = useState<Summary>()
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
  const addSummary = (summary: Summary) => {
    setSummary(summary)
    setStep(4)
  }
  const handleStepClick = (index: number): void => {
    if (index >= step) return;
    setStep(index as CurrentStep)
  }
  if (token === null) {
    // mutation will fail without a valid token
    history.push("/login")
    return <h1>Redirecting to Login</h1>
  }

  const steps = ["Add Source", "Add Quote", "Tag Entities", "Add Summary", "Confirm and Save"]
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
      child = <AddSummary addSummary={addSummary} tags={tags} quote={quote} source={source}/>
      break
    case 4:
      if (!quote || !summary || !tags || !source) return <h1>Oops, shouldnt be here..</h1>
      // reshape tags
      const verifiedTags = tags.filter(tag => tag.type !== "NONE").map(tag => {
        if (tag.type === "PLACE") {
          return {
            type: tag.type,
            id: tag.guid,
            name: tag.name,
            startChar: tag.start_char,
            stopChar: tag.stop_char,
            latitude: tag.latitude,
            longitude: tag.longitude
          }
        }
        return {
          type: tag.type,
          id: tag.guid,
          name: tag.name,
          startChar: tag.start_char,
          stopChar: tag.stop_char
        }
      })
      return (
        <SaveSummary
          annotation={{
            citationId: citationGUID,
            citation: quote.text,
            summaryId: summaryGUID,
            summary: summary.text,
            summaryTags: verifiedTags as PublishNewCitationVars["Annotation"]["summaryTags"],
            meta: source,
            token: token
          }}
        />
          )
  }
  return (
    <Box sx={{margin: 10}}>
      <NavBar children={[
        <ExploreButton />,
        <SettingsButton />
      ]}
      />
      <Stepper activeStep={step}>
        {steps.map((label, index) => (
          <Step key={index} onClick={() => handleStepClick(index)}>
            <StepLabel sx={{color: theme.palette.primary.main}}>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      {child}
    </Box>
  )
}
