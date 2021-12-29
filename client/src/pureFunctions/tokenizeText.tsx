

interface Token {
    startChar: number
    stopChar: number
    word: string
  }

const stopChars = [" ", "\t", "\n", "\x0b", "\x0c"]
const punctuation = ['!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~']

export const tokenize = (text: string): Token[] => {
  const tokenList: Token[] = []
  let lastBoundary: number = 0;
  // iterate through the text
  for (let i: number = 0; i < text.length; i++) {
    if (stopChars.includes(text[i])) {
      // found a boundary
      // make sure this isn't an extra space
      if (lastBoundary === i) {
        lastBoundary += 1
      }
      else {
        tokenList.push({
          startChar: lastBoundary,
          stopChar: i,
          word: text.slice(lastBoundary, i)
        })
        lastBoundary = i + 1
      }
    }
  }
  return tokenList
}
