from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from call_to_crm_agent import build_system_prompt, fake_data
from call_to_crm_agent.agent import run_agent
from call_to_crm_agent.crm import FakeCRM, Note

TODAY = date(2026, 11, 17)  # вторник — фиксированное «сегодня» для всех кейсов
RUNS = 3


class NotesDownCRM(FakeCRM):
    def log_call_note(self, contact_id: str, summary: str) -> Note:
        raise RuntimeError("CRM unavailable: notes service is down")


@dataclass
class EvalCaseResult:
    eval_result: dict[str, bool]
    model_calls: int


@dataclass
class EvalCase:
    name: str
    transcript: Path
    expect_new_contact: bool
    expect_notes: int
    expect_task_dates: list[date]
    build_crm: Callable[[], FakeCRM]
    expect_name: tuple[str, str] | None = None
    expect_company: str | None = None


CASES = [
    EvalCase(
        name="anna_russian",
        transcript=Path("transcripts/anna_russian.txt"),
        expect_new_contact=True,
        expect_notes=1,
        expect_task_dates=[
            date(2026, 11, 17),
            date(2026, 11, 19),
        ],
        expect_name=("Anna", "Smirnova"),
        build_crm=fake_data.build_fake_crm,
    ),
    EvalCase(
        name="anna_notes_down",
        transcript=Path("transcripts/anna_new_contact.txt"),
        expect_new_contact=True,
        expect_notes=0,
        expect_task_dates=[
            date(2026, 11, 17),
            date(2026, 11, 19),
        ],
        build_crm=lambda: NotesDownCRM([fake_data.get_default_john_doe_contact()]),
    ),
    EvalCase(
        name="anna_new_contact",
        transcript=Path("transcripts/anna_new_contact.txt"),
        expect_new_contact=True,
        expect_notes=1,
        expect_task_dates=[
            date(2026, 11, 17),
            date(2026, 11, 19),
        ],
        build_crm=fake_data.build_fake_crm,
    ),
    EvalCase(
        name="john_acme_mismatch",
        transcript=Path("transcripts/john_acme_mismatch.txt"),
        expect_new_contact=False,
        expect_notes=1,
        expect_task_dates=[
            date(2026, 11, 20),
            date(2026, 11, 20),
            date(2026, 11, 24),
        ],
        expect_company="Example Inc.",
        build_crm=fake_data.build_fake_crm,
    ),
]


def run_case(client: anthropic.Anthropic, case: EvalCase) -> EvalCaseResult:
    crm = case.build_crm()
    transcript = case.transcript.read_text(encoding="utf-8")

    messages = run_agent(
        client,
        crm,
        build_system_prompt(TODAY),
        transcript,
    )

    contact = crm.contacts[-1]
    company = crm.contacts[0].company
    new_contact_created = len(crm.contacts) == 2
    task_dates = sorted(task.due_date for task in crm.tasks)

    if task_dates != case.expect_task_dates:
        print(
            f"DATES MISMATCH {case.name}: expected {case.expect_task_dates}, got {task_dates}"
        )

    model_calls_count = 0
    for message in messages:
        if message["role"] == "assistant":
            model_calls_count += 1

    eval_result = {
        "contact": new_contact_created == case.expect_new_contact,
        "notes": len(crm.notes) == case.expect_notes,
        "dates": task_dates == case.expect_task_dates,
    }

    if case.expect_company is not None:
        eval_result["company"] = company == case.expect_company

    if case.expect_name is not None:
        actual = (contact.first_name, contact.last_name)
        if actual != case.expect_name:
            print(
                f"NAME MISMATCH {case.name}: expected {case.expect_name}, got {actual}"
            )
        eval_result["name"] = actual == case.expect_name

    return EvalCaseResult(
        eval_result=eval_result,
        model_calls=model_calls_count,
    )


def main() -> None:
    load_dotenv()
    client = anthropic.Anthropic()

    summary = []

    for case in CASES:
        model_calls_total_for_case = 0

        passed: dict[str, int] = {}

        for i in range(1, RUNS + 1):
            print(f"=== {case.name} run {i}/{RUNS} ===")

            result = run_case(client, case)

            model_calls_total_for_case += result.model_calls
            print(f"Model calls: {result.model_calls}")

            for check_name, ok in result.eval_result.items():
                passed.setdefault(check_name, 0)
                if ok:
                    passed[check_name] += 1
        summary.append((case.name, passed, model_calls_total_for_case))

    for name, passed, model_calls_total in summary:
        line = "  ".join(f"{check} {count}/{RUNS}" for check, count in passed.items())
        print(f"{name:<22}{line}  calls avg {model_calls_total / RUNS:.1f}")


if __name__ == "__main__":
    main()
