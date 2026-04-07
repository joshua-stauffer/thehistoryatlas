---
name: prompt-tuning
description: Run a prompt tuning experiment for the text reader extraction pipeline
allowed-tools: Bash(source:*), Bash(python:*), Read, Write, Edit, Glob, Grep
---

# Prompt Tuning Experiment

Run a prompt tuning experiment using the Message Batches API against a PDF text chunk.

## Usage

`/prompt-tuning [args]`

Arguments are passed directly to the experiment script. Common patterns:

- `/prompt-tuning --runs 5 --label baseline` — run baseline with default prompt
- `/prompt-tuning --runs 5 --label v2 --prompt-file text_reader/experiments/prompts/v2.txt` — test a prompt variant
- `/prompt-tuning --runs 5 --label test --start-page 534 --end-page 538` — test different pages

## Execution

```bash
cd /Users/josh/dev/thehistoryatlas
source env/bin/activate
python text_reader/experiments/prompt_tuning.py $ARGUMENTS
```

The script:
1. Extracts text from the Grove's Dictionary PDF (pages 168-172 by default)
2. Submits N identical extraction requests as a Message Batch (50% cost discount)
3. Polls until complete
4. Validates each extracted event (checks person/place/time names appear verbatim in summary)
5. Reports per-run and aggregate statistics
6. Saves results to `text_reader/experiments/results/<label>.json`

## Key files

- Script: `text_reader/experiments/prompt_tuning.py`
- Prompts: `text_reader/experiments/prompts/`
- Results: `text_reader/experiments/results/`
- PDF source: `text_reader/sources/Grove's_dictionary_of_music_and_musicians_3.pdf`
- API key: loaded from `.env.local` (`CLAUDE_API_KEY`)

## After running

Compare results across experiments. The key metric is **Valid%** — the percentage of extracted events where all entity names (person, place, time) appear as literal substrings in the summary.
