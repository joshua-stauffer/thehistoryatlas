
import { EntityType } from "../types";

export const prettifyType = (type: EntityType): string => {

  switch (type) {

    case "PERSON":
      return "person"

    case "PLACE":
      return "place"
    
    case "TIME":
      return  "time"
  }
}