
interface PrettifyDateProps {
  dateString: string;
  // TODO: allow for region/language specific date presentations
}

export const prettifyDate = (props: PrettifyDateProps) => {
  const { dateString } = props;
  const dates = dateString.split('|')
  switch (dates.length) {

    case 1:
      return dates[0]

    case 2:
      return  getSeasonString(dates[1]) + ' ' + dates[0]

    case 3:
      return getMonthString(dates[2]) + ' ' + dates[0]

    case 4:
      return getMonthString(dates[2]) + ' ' + getDayString(dates[3]) + ', ' + dates[0]
  }
}

const getSeasonString = (season: string): string => {
  
  switch (season) {
    case '1':
      return 'Winter'

    case '2':
      return 'Spring'

    case '3':
      return 'Summer'

    case '4':
      return 'Fall'

    default:
      throw new Error(`Unknown season ${season} passed to getSeasonString`)
  }
}

const getMonthString = (month: string): string => {

  switch (month) {

    case '1':
      return 'January'    
      
    case '2':
      return 'February'

    case '3':
      return 'March'    
      
    case '4':
      return 'April'

    case '5':
      return 'May'    
      
    case '6':
      return 'June'

    case '7':
      return 'July'

    case '8':
      return 'August'

    case '9':
      return 'September'

    case '10':
      return 'October'

    case '11':
      return 'November'

    case '12':
      return 'December'

    default:
      throw new Error(`Unknown month ${month} passed to getMonthString`)
    }
}

const getDayString = (day: string): string => {
  if (day.startsWith('1')) {
    return day + 'th'
  } else if (day.endsWith('1')) {
    return day + 'st'
  } else if (day.endsWith('2')) {
    return day + 'nd'
  } else if (day.endsWith('3')) {
    return day + 'rd'
  } else {
    return day + 'th'
  }
}
