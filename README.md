# Call-to-CRM Agent

An LLM agent that turns a business call transcript into CRM records: it finds or creates the contact, logs a call note, and creates a follow-up task for every commitment made during the call.

The model (Claude, via the Anthropic API) decides which CRM tools to call; the code executes them against a real CRM (HubSpot) or an in-memory fake one.

## Example

Input (`transcripts/anna_new_contact.txt`):

> Anna Smirnova from Blue Sky called, +995 599 000 111. She's interested in a plan for a team of 20 people. She asked us to send a commercial proposal and call her back on Thursday.

Run on HubSpot (Tuesday, 2026-11-17), trimmed:

```text
Executing tool: 'find_contact' with args: '{'phone': '+995599000111'}'
Tool success: []
Executing tool: 'create_contact' with args: '{'first_name': 'Anna', 'last_name': 'Smirnova', 'phone': '+995599000111', 'company': 'Blue Sky'}'
Executing tool: 'log_call_note' with args: '{'contact_id': '927893414126', 'summary': 'Call date: 2026-11-17. ...'}'
Executing tool: 'create_task' with args: '{..., 'title': 'Send commercial proposal to Anna Smirnova (Blue Sky) ...', 'due_date': '2026-11-18'}'
Executing tool: 'create_task' with args: '{..., 'title': 'Call back Anna Smirnova (Blue Sky) regarding the commercial proposal', 'due_date': '2026-11-19'}'

CRM PROCESSING SUMMARY
Contact: Anna Smirnova (Blue Sky)
Contact status: New contact created
CRM note: Created
Tasks created: 2
...
Assumptions:
- "Thursday" is 2026-11-19, the next Thursday after today (Tuesday, 2026-11-17).
```

The note and both tasks were requested by the model in a single response, so the whole run took three model calls.

## How it works

```text
transcript.txt ──► run_agent ──► Claude (system prompt + tool definitions)
                      ▲                  │ tool_use blocks
                      │                  ▼
                      │           execute_tool  ──►  CRM (Protocol)
                      │                  │            ├─ HubSpotCRM ──► HubSpot REST API
                      └── tool_result ◄──┘            └─ FakeCRM (in memory, for tests)
```

1. The transcript is sent to the model together with a system prompt (today's date and weekday, workflow, policies, report format) and four tool definitions.
2. While the model answers with `stop_reason == "tool_use"`, the agent runs every requested tool and sends all results back in one message, including errors (`is_error`), so the model can react to them.
3. The loop ends when the model writes its final report. A step limit and an explicit `max_tokens` check stop the run before a cut-off tool call is executed.

### Tools

| Tool | What it does |
|---|---|
| `find_contact` | Searches contacts by phone; returns a list (empty = not found) |
| `create_contact` | Creates a contact; the phone is validated and stored in E.164 |
| `log_call_note` | Adds a call summary note to the contact |
| `create_task` | Adds a follow-up task with a due date (`YYYY-MM-DD`) |

### Agent policies

Behaviour the agent follows on purpose, written into the system prompt:

- **Autonomous:** never asks questions; assumptions go into the final report.
- **CRM data wins:** if the call contradicts the CRM (e.g. a contact mentions a new company), the CRM record is not overwritten; the discrepancy goes into the note and the report.
- **One commitment = one task**, each with an explicit date; relative dates ("next Tuesday") are resolved against today's date.
- **Preparation tasks** are due 2 working days before the event they prepare for, never earlier than today.
- **Partial failure:** if one operation fails, the others still run; the report says what failed.
- **Language:** the transcript may be in any language; names are stored in Latin script, notes, task titles and the report are written in English.

## Project layout

```text
src/call_to_crm_agent/
  __init__.py   # entry point: reads the transcript, picks the CRM, builds the system prompt
  agent.py      # the agent loop
  tools.py      # tool definitions for the model + thin adapters to the CRM
  crm.py        # domain dataclasses, CRM Protocol, FakeCRM
  hubspot.py    # HubSpot API client, mappers, HubSpotCRM
  phones.py     # phone parsing/normalisation (libphonenumber)
tests/          # pytest, no network or API keys needed
transcripts/    # sample calls: new contact, CRM mismatch, Russian-language call
```

## Getting started

Requirements: [uv](https://docs.astral.sh/uv/) (it installs Python 3.14 itself) and an [Anthropic API key](https://console.anthropic.com/). A HubSpot account is optional: the fake CRM works without it.

```bash
git clone https://github.com/Windman/call-to-crm-agent.git
cd call-to-crm-agent
uv sync
```

Create a `.env` file in the project root (it is git-ignored):

```dotenv
ANTHROPIC_API_KEY=sk-ant-...
HUBSPOT_TOKEN=...      # only for CRM=hubspot
CRM=fake               # fake | hubspot (default: hubspot)
```

### Run

```bash
# In-memory CRM (contains one contact, John Doe, +995 555 123 456)
CRM=fake uv run call-to-crm-agent transcripts/john_acme_mismatch.txt

# Real HubSpot
CRM=hubspot uv run call-to-crm-agent transcripts/anna_new_contact.txt
```

On Windows, use `uv run python -m call_to_crm_agent transcripts/<file>.txt` and set the variable with `$env:CRM="fake"` in PowerShell.

### HubSpot setup

1. Create a free HubSpot CRM account.
2. Create a **service key** (Development → Keys → Service keys) with the scopes `crm.objects.contacts.read` and `crm.objects.contacts.write`. These two scopes are enough for notes and tasks associated with a contact.
3. Put the key into `.env` as `HUBSPOT_TOKEN`.

Task due dates are sent as 09:00 in the business time zone (`Asia/Tbilisi` by default, configurable in `HubSpotCRM`).

## Tests

```bash
uv run pytest          # 35 tests, offline
uv run ruff check
```

The agent loop, tools, phone handling and HubSpot mappers are tested without network access: the CRM is a `FakeCRM`, HubSpot mappers are tested on trimmed real API responses, and the model client is replaced by a stub.

## Design notes

- **The agent doesn't know which CRM it talks to.** Tools depend on a small `CRM` Protocol; `HubSpotCRM` and `FakeCRM` implement it, and `main()` picks one via the `CRM` environment variable.
- **Model output is untrusted input.** Tools parse arguments once at the boundary (`date.fromisoformat`, phone → E.164) and the CRM layer only receives typed values. Invalid input becomes a tool error the model can see and fix.
- **Tool error text is part of the prompt.** Errors are returned to the model with the exception type and message, not swallowed.
- **Dates are not instants.** A task's due date is a calendar `date` in the domain; only the HubSpot adapter turns it into a timestamp in the business time zone.
- **Encode at the boundary.** Notes are plain text in the domain; the HubSpot adapter HTML-escapes them and converts line breaks to `<br>`, because HubSpot stores note bodies as HTML.

## Roadmap

- [ ] Evals: a set of transcripts with expected contacts, tasks and dates, and a script that scores the agent
- [ ] Better HubSpot error handling: response body in tool errors, `409` for duplicate emails, retries on `429`, idempotent retries
- [ ] FastAPI backend + Next.js UI that shows each agent step
- [ ] Dockerfile
