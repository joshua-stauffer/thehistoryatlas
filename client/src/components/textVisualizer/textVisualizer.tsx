import { useState } from "react";
import { Container, AnnotateButton, Place, NonEntity } from "./style";

interface TextVisualizerProps {
  chunkedText: {
    text: string;
  }[];
}

enum EntityChoices {
  NONE = "NONE",
  PERSON = "PERSON",
  PLACE = "PLACE",
  TIME = "TIME",
}

export const TextVisualizer = ({ chunkedText }: TextVisualizerProps) => {
  const [currentEntityType, setCurrentEntityType] = useState(
    EntityChoices.NONE
  );

  return (
    <Container>
      <AnnotateButton
        onClick={() => setCurrentEntityType(EntityChoices.PERSON)}
      >
        Person
      </AnnotateButton>
      <AnnotateButton onClick={() => setCurrentEntityType(EntityChoices.PLACE)}>
        Place
      </AnnotateButton>
      <AnnotateButton onClick={() => setCurrentEntityType(EntityChoices.TIME)}>
        Person
      </AnnotateButton>
      <AnnotateButton onClick={() => setCurrentEntityType(EntityChoices.NONE)}>
        Reset
      </AnnotateButton>
    </Container>
  );
};
