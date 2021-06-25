import { useState } from "react";
import { CitationButton } from "./style";
import { FaChevronUp, FaChevronDown } from 'react-icons/fa';
import { CitationCard } from './citationCard';

interface CitationProps {
  guid: string;
}

export const Citation = ({ guid }: CitationProps) => {
  const [ isOpen, setIsOpen ] = useState(false);

  return (
    <>
    <CitationButton
      onClick={() => setIsOpen(cur => !cur)}
    >
      Citation { isOpen ? <FaChevronUp /> : <FaChevronDown />}
    </CitationButton>
    {isOpen ? <CitationCard citationGUID={guid} /> : null}
    </>
  )
}