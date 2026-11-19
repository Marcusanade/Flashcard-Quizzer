# AI Edit Log

**Instructions:** Use this document to track all your interactions with AI assistants during the project. This log will help you reflect on your AI collaboration process and demonstrate your learning journey.

## How to Use This Log

For each AI interaction, create a new entry with the following structure:

### Entry Template
```
## [Date] - [Brief Description]

**Context:** What were you trying to accomplish?
**AI Tool Used:** Claude/ChatGPT/Copilot/etc.
**Prompt/Request:** What exactly did you ask the AI?
**AI Response:** Summary of what the AI generated (don't copy entire code blocks)
**Changes Made:** What modifications did you make to the AI's suggestions?
**Reasoning:** Why did you make those changes?
**Outcome:** What was the final result?
**Lessons Learned:** What did you learn from this interaction?
```

---

## Example Entry

> This entry shows the expected level of detail. It does **not** count toward your five required entries. Delete it before you submit.

### 2024-01-15 - Flashcard Loader Validation

**Context:** I needed a module that loads flashcards from a JSON file and rejects bad data with a clear message instead of a traceback.

**AI Tool Used:** Claude Code

**Prompt/Request:** "Create `data_loader.py` with a function that loads flashcards from a JSON file. Support both a plain list of `{"front", "back"}` objects and a `{"cards": [...]}` wrapper. Raise a custom exception with a helpful message if the file is missing, the JSON is malformed, or a card has no `back`. Use type hints."

**AI Response:** Claude generated a `load_flashcards()` function and a `FlashcardLoadError` exception. It handled both JSON formats and a missing file, but it caught every exception with a bare `except:` and only checked for `front`.

**Changes Made:** 
- Replaced the bare `except:` with specific `FileNotFoundError` and `json.JSONDecodeError` handlers
- Added validation that every card has non-empty `front` and `back` strings
- Added the card's position to the error message so the user can find the bad entry

**Reasoning:** 
- A bare `except:` hides real bugs, including `KeyboardInterrupt`
- A card without a `back` would break the quiz loop later, far from the cause
- A message that names the bad card is far easier to act on

**Outcome:** The loader now rejects bad decks with one readable line, and `test_load_missing_required_field` passes.

**Lessons Learned:** 
- AI covered the happy path well but under-specified the error handling
- Naming the exact failure cases in the prompt produced better code than asking for "error handling"
- Each requirement in the prompt should map to a test

---

## Your Log Entries

### 2026-11-17 - Tooling configuration and Definition of Done (Prompt 0)

**Context:** Before generating any application code, I wanted the quality tools (flake8, black, isort, mypy) configured and the project's Definition of Done written into `.claude/CLAUDE.md`. That way every later AI-generated change could be checked against the same rules from the start. I also wanted the AI to read the starter guides and propose an architecture without writing any application code.

**AI Tool Used:** Claude Code in VS Code. The prompt was drafted with a separate Claude chat session used as a planning assistant.

**Prompt/Request:** The prompt was sent in Spanish (a mistake, see below). In summary: read `.claude/CLAUDE.md`, the two files in `ai_guidance/`, `docs/design_patterns.md`, `docs/report_template.md` and `data/*.json`; summarize the review checklist and the Strategy and Factory patterns in at most 10 lines; create `.flake8` (max-line-length 88), `pyproject.toml` (black line-length 88, isort profile "black") and `mypy.ini` (`disallow_untyped_defs = True`); add a "Definition of Done del proyecto" section to `.claude/CLAUDE.md` (modular architecture, QuizMode ABC with three strategies plus a factory, type hints everywhere, argparse instead of click, own validation instead of pydantic, pytest with more than 80% coverage, clean flake8/black/mypy, every AI interaction logged); propose a file structure without implementing it and flag any ambiguity in the starter.

**AI Response:** Claude Code read the documents and created the three configuration files. It added `extend-ignore = E203, W503` to `.flake8` (not requested, but the standard setting for using flake8 with black) and pinned `python_version = 3.14` in `mypy.ini`. It appended the Definition of Done section to `CLAUDE.md`, written in Spanish. It proposed `main.py`, `data_loader.py`, `models.py`, `quiz_engine.py`, `ui.py` and `utils/file_handler.py`. Instead of guessing, it flagged ambiguities: `utils/` versus the project root, the "do not create a venv" line in `CLAUDE.md` versus my local venv, the outdated README, mypy support for Python 3.14, and the missing specification for the adaptive mode. It did not run any tool.

**Changes Made:**
- Sent a follow-up prompt asking Claude Code to translate the Definition of Done section into English, keep its structure, change nothing else and end the file with a trailing newline (commit `73504b7`)
- Checked the commit with `git show`: the single "removed" line in `CLAUDE.md` was the same sentence re-added, and only the missing end-of-file newline had changed
- Sent a second small prompt to add a "Local Environment (Windows)" note to `CLAUDE.md`, because the file said not to create a virtual environment while I use a local venv. I checked with `git diff` that only 11 lines were added and none removed
- Accepted `extend-ignore = E203, W503` and the non-strict `mypy.ini`
- Recorded two decisions to apply through the next prompts: remove `python_version` from `mypy.ini`, and use the exact test file names required by the project specification

**Reasoning:**
- The language of a prompt sets the language of the output. A Spanish section inside an English `CLAUDE.md` would be inconsistent in the file the agent reads at the start of every session
- Claude Code reported adding a section, but the AI's summary is not proof of what changed on disk, so I verified the diff myself
- The flake8 exceptions prevent false errors caused by black, and the final submission requires zero flake8 errors
- Pinning `python_version = 3.14` risks failures if mypy does not fully support that version yet
- The instruction about the virtual environment was written for the course cloud workspace, and following it literally on my machine could lead the agent to install packages outside my venv

**Outcome:** Tooling configuration, the Definition of Done in English and the local environment note are committed and pushed to GitHub. The architecture is agreed and the open questions are listed, so the first code prompt can start from clear decisions.

**Lessons Learned:**
- The AI mirrors the language of the prompt, so prompts must be written in the language of the target files
- Verifying with `git diff` or `git show` is what catches small gaps between what the AI says and what it does
- Asking the AI to read first and flag ambiguities produced useful questions instead of invented answers
- The AI added a setting I did not ask for (`extend-ignore`). It was correct here, but every unrequested addition needs a review
- The first prompt did not follow the Requirements Prompt pattern from `ai_guidance/` (Context, Requirements, Constraints, Examples) and was written in Spanish. From now on, prompts follow that pattern in English

### 2026-11-18 - Configuration cleanup and verification (Phase 1)

**Context:** After the first commit of the quality tooling, I reviewed each configuration file (`.flake8`, `pyproject.toml`, `mypy.ini`) against the real file on disk, not against Claude Code's summary. I used small prompts for each fix and verified every change with `git diff` and the tools themselves before committing.

**AI Tool Used:** Claude Code in VS Code, plus a separate Claude chat session as a planning assistant.

**Prompt/Request:** Three small prompts, each with Context, Requirements and Constraints, in English:
1. Remove the redundant `line_length = 88` from `[tool.isort]`, because `profile = "black"` already sets it, and confirm with `isort --show-config` that the value is still 88.
2. Add `.claude` to the isort `skip` list, because isort printed `UserWarning: Unable to parse file ... 'charmap' codec` for the emoji-containing, extensionless files in `.claude/commands/`.
3. Change `python_version` in `mypy.ini` from 3.14 to 3.10, and if mypy rejected 3.10, stop and report the exact error instead of choosing another value.

**AI Response:** All three changes were correct on the first attempt. Each diff was exactly the lines requested. For the second prompt, Claude Code reported that `isort --check .` ended with exit code 0 and only `Skipped 2 files`, and said openly that it had not run the check before the change, so it had not seen the original warnings. It also reported running the tools through `.\venv\Scripts\python.exe`, because the `python` in its terminal was the global one without isort.

**Changes Made:**
- Accepted all three diffs without modification
- Committed the isort changes together (`2460ddf`) and the mypy change separately (`b4f80cb`)
- Re-ran `isort --check .` and `black --check .` in my own terminal with the venv active to confirm the warnings were gone

**Reasoning:**
- The `charmap` warnings only appeared when I ran the check myself. Neither the AI nor I predicted them from the diff, so verification with the real tools mattered more than reading the diff
- Claude Code does not inherit my activated virtual environment. A future "No module named ..." error from the agent will most likely come from this
- I first planned to remove `python_version` entirely to avoid a possible mypy problem with Python 3.14. After checking that mypy 2.4.1 works with 3.14, that risk did not exist. I then pinned 3.10 because the specification requires Python 3.10 or higher, so mypy can flag features that would fail on the minimum version
- Telling the AI to stop and report if 3.10 was rejected kept it from silently picking another value

**Outcome:** The three configuration files are verified and consistent: line length 88 in black and flake8, isort inheriting it from the black profile, and mypy targeting Python 3.10. `black --check`, `isort --check` and `mypy` all finish clean. In the same phase, I settled the architecture and the rules of the adaptive mode (rest between repetitions proportional to the deck size and a card retired after 3 failures) with the planning assistant, before writing any code prompt.

**Lessons Learned:**
- Verifying with the real tools in my own environment catches side effects that a correct-looking diff hides
- An AI agent runs in its own environment, which may differ from mine (virtual environment, encoding)
- Asking the AI to stop and report when a condition fails is safer than letting it improvise
- Small prompts with one change each produced correct results and made review quick
- An AI that states what it did not check is easier to trust and tells me where to verify


### 2026-11-18 - Data layer: Flashcard model, file reader and loader (Prompts 1A and 1B)

**Context:** I needed a data layer that turns a JSON deck into validated `Flashcard` objects and reports every problem as a readable one-line message instead of a traceback. I split the work into two small prompts, as recommended in `ai_guidance/prompting_best_practices.md`, instead of one large prompt: 1A for the model and the low-level file reader, and 1B for the loader and its validation.

**AI Tool Used:** Claude Code in VS Code, plus a separate Claude chat session as a planning assistant to draft the prompts.

**Prompt/Request:** Both prompts followed the Requirements Prompt pattern from `ai_guidance/` (Context, Requirements, Constraints, Examples), in English, and ended with a Verification section.
- Prompt 1A: create `models.py` with a frozen dataclass `Flashcard(front, back)` and `utils/file_handler.py` with `read_text_file(path)`. It had to read with `encoding="utf-8-sig"`, explicitly raise `IsADirectoryError` for directories (because opening a directory raises `PermissionError` on Windows), and not catch any exception.
- Prompt 1B: create `data_loader.py` with `load_flashcards(path)` and `FlashcardLoadError`. It accepted the array and the `{"cards": [...]}` formats and named 15 exact failure cases (empty path, missing file, directory, permissions, invalid UTF-8, other OS errors, malformed JSON with line and column, wrong root, `cards` not a list, empty deck, card not an object, missing `front`, missing `back`, non-string fields, empty or blank fields). It also required the `except` order (specific exceptions before `OSError`), `raise ... from error`, positions counted from 1, `strip()` on the texts, small private helper functions, no printing and no `sys.exit`.
- Both prompts told the agent to run every tool through `.\venv\Scripts\python.exe -m ...` and to report the exact results.

**AI Response:** For 1A, Claude Code created both files, with docstrings in Google style, and said it had not tested the BOM case yet. For 1B, it created `data_loader.py` with `load_flashcards`, `FlashcardLoadError` and five private helpers. It covered all the named cases, used `raise ... from error` everywhere and listed the exact message of each case. It tested every case it could reproduce on Windows with a throwaway script in the system temp folder, deleted afterwards. It reported openly that the permission error and the generic OS error cases could not be reproduced reliably, so those two branches were untested. It also noticed that `models.py` and `utils/file_handler.py` had been committed between the two prompts.

**Changes Made:**
- No code changes were needed. I accepted both results as generated (commits `ab580d2` and `6805568`)
- The improvements happened before running the prompts: splitting the work into small prompts, naming every failure case, fixing the `except` order and adding the explicit directory check
- I left two edge cases unhandled on purpose and noted them as known limitations: a JSON with extreme nesting raises `RecursionError`, and an empty `Path` object (not a string) is treated as the current directory

**Reasoning:**
- A card without a `back` would break the quiz far from the cause, so the loader must reject it at load time with its position
- Listing each failure case worked better than asking for "error handling", which is what the template example in the log also teaches
- A real deck will never have thousands of nested brackets, and from the command line the path is always a string, so handling those cases would add code without real benefit
- `utf-8-sig` was chosen over `utf-8` because Windows editors can save a BOM that breaks `json.loads`, and it behaves the same on Linux

**Outcome:** The data layer works. `data/glossary.json` (array format) loads 10 cards and `data/python_basics.json` (object format) loads 8. All the reproducible errors produce a single readable line, and a deck with and without BOM loads the same. `black`, `isort`, `flake8` and `mypy` pass. The permission error, the generic OS error and the BOM case will be covered by tests in the next prompt.

**Lessons Learned:**
- Naming every failure case and the order of the `except` blocks in the prompt produced correct code on the first attempt
- A platform detail, such as the different error when opening a directory on Windows, is easy to miss, so stating it in the prompt avoided behavior that would differ between systems
- Combining the agent's own smoke tests with my commands gave two independent confirmations
- The agent clearly said which branches were untested, and that tells me exactly where the tests must go
- Splitting work into small prompts made each review short and each commit easy to explain


### 2026-11-18 - Data layer tests and a review gap (Prompts 1C and 1D)

**Context:** The data layer was committed without tests. I asked Claude Code for the tests in two small prompts: 1C for `data_loader.py` and 1D for `models.py` and `utils/file_handler.py`. I added 1D after reviewing the 1C result and finding a gap that the coverage number hid.

**AI Tool Used:** Claude Code in VS Code, plus a separate Claude chat session as a planning assistant to draft the prompts and review the results.

**Prompt/Request:** Both prompts followed the Requirements Prompt pattern (Context, Requirements, Constraints, Examples) in English, with a Verification section.
- Prompt 1C: create `tests/test_flashcard_loader.py` with the four test names required by the course, one test for each of the 15 failure cases, tests for the BOM, the exception chaining and the real decks. The Context listed the exact error messages, so the tests would check text instead of guessing it. It required patching `data_loader.read_text_file` (and not `utils.file_handler`) to simulate permission and OS errors, because `data_loader` imports the function by name.
- Prompt 1D: create `tests/test_models.py` and `tests/test_file_handler.py` to test each module on its own: immutability, equality and hashing of `Flashcard`, and the BOM, non-ASCII text, directory and invalid UTF-8 behavior of `read_text_file`.
- Both prompts said: if a test fails because of a real bug, do not change the source code and report it, do not weaken a test to make it pass, and run the tools through the venv Python. Both asked for a mutation check: break the code on purpose and confirm that tests fail.

**AI Response:** For 1C, Claude Code created 48 tests, all passing, with 100% coverage on the three modules. For the mutation check it changed `enumerate(raw_cards, 1)` to `enumerate(raw_cards, 0)`, saw 20 tests fail, and restored the file. For 1D it created 18 more tests (66 in total). Changing `utf-8-sig` to `utf-8` made 2 tests fail, and removing `frozen=True` made 5 fail. After restoring both files, `git diff` was empty. It reported that it could not test the code on Python 3.10 because the venv uses 3.14, and that it did not add this log entry because I had told it not to modify existing files. In the 1D run, its writing tool turned the escape `"\ufeff"` into a literal invisible BOM character, isort reported it, and Claude Code restored the escape sequence.

**Changes Made:**
- Accepted the 1C tests as generated. I reviewed the file against the prompt: the required names, one test per failure case, message assertions, the patched name, type hints, and no `# type: ignore` or `unittest.mock`
- Added prompt 1D after the review. All tests in 1C reached `models.py` and `utils/file_handler.py` only through the loader, so the immutability of `Flashcard` and the directory check were not tested directly, even though coverage showed 100%
- Verified the mutation counts myself by counting which 1C tests assert "Card 1": 19, plus the position test, gives the 20 failures that Claude Code reported
- Accepted the correction that the AI made to the `\ufeff` escape, and confirmed it in the file I received

**Reasoning:**
- A coverage percentage measures executed lines, not whether each behavior is checked. Mutation checks show that the tests can fail
- The test that put two identical cards in a set documents that duplicate cards are indistinguishable. This matters for the adaptive mode, which must not use the card itself as the key of a failure counter
- Forbidding changes to the source code when a test fails keeps real bugs visible instead of hiding them behind an edited test
- The total coverage of 100% includes the test files and the empty `__init__.py` files, so it overstates the result

**Outcome:** 66 tests pass, with 100% coverage on `data_loader.py`, `models.py` and `utils/file_handler.py`, and black, isort, flake8 and mypy are clean. The data layer is complete. The permission and generic OS error branches, which the first loader prompt could not test, are now covered by simulating the errors. The tests are in commits `0030fe7` (loader tests, 1C) and `2577d30` (model and file handler tests, 1D).

**Lessons Learned:**
- High coverage can hide an untested behavior, so I check what each test asserts and not only the percentage
- A deliberate code change that makes tests fail is a quick way to know that the tests protect something
- Giving the exact error messages in the prompt produced tests that check real text
- Telling the AI to report a failing test instead of changing the source code keeps the review in my hands
- An AI tool can alter a file in a way that is invisible when reading, such as an escape turned into a literal character, and the quality tools caught it
- Asking for the testing of each module separately from the module that uses it gave tests that explain what each part must do


### 2026-11-18 - Strategy and Factory patterns: quiz engine (Prompts 2A and 2B)

**Context:** I needed the quiz engine without screen or keyboard code, so that it can be tested alone. I applied the Strategy pattern to the three quiz modes (sequential, random, adaptive) and the Factory pattern to choose the mode from the `--mode` name. I split the work into two small prompts: 2A for `QuizMode` and the three modes (18 November), and 2B for the factory and the session that uses a mode (19 November). I planned the design with a separate Claude chat session after reading `docs/design_patterns.md`.

**AI Tool Used:** Claude Code in VS Code, plus a separate Claude chat session as a planning assistant to draft the prompts and review the results.

**Prompt/Request:** Both prompts followed the Requirements Prompt pattern (Context, Requirements, Constraints, Examples) in English, with a Verification section.
- Prompt 2A: create `quiz_engine.py` with an abstract `QuizMode` (`next_card()` abstract and `record_result()` as an empty hook), `SequentialMode`, `RandomMode` with an injected random generator, `rest_for_deck_size()` and `AdaptiveMode`. The adaptive rules were written exactly: a failed card comes back after a rest that grows with the deck size, a card is retired after 3 failures, the same card is never served twice in a row if there is another candidate, and cards are identified by position and never by value, so two cards with the same text do not share a failure counter. The prompt listed deliberate differences from the guide: every method has a return type (the guide omits `-> None`, which mypy rejects), modern `list` and `dict` instead of the `typing` aliases, and no `set_strategy` method, because the mode is chosen once.
- Prompt 2B: add `QuizModeFactory` as a class with a registry (the shape used in the guide), `is_correct_answer`, the dataclasses `AnswerResult` and `SessionStats`, and `QuizSession` as the context of the Strategy pattern. It defined the statistics: total questions counts every time a card is asked, repetitions included; accuracy is correct answers over total; missed terms are distinct, in order of first miss.
- I calculated the expected results by hand before seeing any code (for example the adaptive sequence A, B, C, D, B, E, B, and 4 correct of 7, which is 57.14%) and put them in the Verification section.

**AI Response:** For 2A, Claude Code created `quiz_engine.py`, and all 11 verification checks matched my hand-calculated sequences. It reported three decisions of its own: the last served card is never repeated even if its rest has finished, `record_result` compares cards by value, and an empty deck is checked before the other parameters. For 2B it added the factory, the function, the two dataclasses and the session, and all 10 checks passed. It also reported, in its summary, that `is_correct_answer` returned False for `"a b"` against `"a b"`, which cannot be right for identical strings.

**Changes Made:**
- Chose the factory as a class and not as a function, because it follows the shape of the guide and is recognizable when someone inspects `quiz_engine.py`
- Accepted the three decisions of the 2A report after tracing the adaptive sequences by hand
- Found a mismatch while reviewing the 2B code: the docstring of `is_correct_answer` said that an empty answer is incorrect, but the code only compared the two strings, so `is_correct_answer("", "")` returned True. I sent a correction prompt instead of editing the code by hand: return False when the answer is empty after `strip()`, change nothing else, and print the results with `repr()` so spaces are visible
- Checked the corrected function myself by reading its last lines and the seven test cases
- Explained the strange `"a b"` result: the case actually had two spaces in the first argument, and the report text had collapsed them. The `repr()` output showed `'a  b'` returning False and `'a b'` returning True
- Made one commit for the 2B work and the correction (`75cf67b`)

**Reasoning:**
- A docstring that promises a behavior the code does not have is a bug in the contract. The function is public, and the rest of the code may rely on its documentation, even if the loader makes this input impossible today
- Printing with `repr()` is needed whenever the point of a check is whitespace
- Identifying cards by position, and not by value, follows from a test written in the data layer, which shows that two cards with the same text are indistinguishable
- The guide stays useful as a structure, but its code cannot be copied, because it conflicts with the type rules of this project

**Outcome:** The Strategy and Factory patterns are in `quiz_engine.py` (commits `d2a7b1d` and `75cf67b`). The three modes are interchangeable through `QuizMode`, `QuizModeFactory.create_mode` returns a new instance on every call, and `QuizSession` computes total questions, accuracy and missed terms without any input or output. `black`, `isort`, `flake8` and `mypy` pass, and the 66 existing tests still pass. The engine has no tests of its own yet, which are the next prompt.

**Lessons Learned:**
- Calculating the expected results by hand before reading the code gives an independent check, so I am not just comparing the AI with itself
- The review caught a gap between a docstring and the code that all the tools missed. Type checkers and linters do not read promises
- When the AI shows a result that cannot be right, I should look for a display problem before suspecting the code, and `repr()` is the way to see it
- The AI cannot isolate a diff for a correction if the previous work is not committed. I should commit before asking for a diff
- A design guide gives a structure, but its examples may break the project rules, so the prompt must list the deliberate differences
- The agent was honest about what it could not do, such as isolating that diff, and did not invent output


### 2026-11-19 - Quiz engine tests and mutation checks (Prompt 2C)

**Context:** The quiz engine (`QuizMode` and its three subclasses, `QuizModeFactory` and `QuizSession`) was committed without tests. The course requires `test_quiz_mode_factory` and `test_adaptive_mode_behavior`, and I wanted tests that protect the design decisions of the adaptive mode, not just tests that execute the lines.

**AI Tool Used:** Claude Code in VS Code, plus a separate Claude chat session as a planning assistant to draft the prompt and review the result.

**Prompt/Request:** One prompt in English, with the Requirements Prompt structure (Context, Requirements, Constraints, Examples) and a Verification section. It created two files, `tests/test_quiz_modes.py` for the modes and the factory and `tests/test_quiz_session.py` for the answer check, the statistics and the session.
- The Context listed the exact behavior and error messages of the engine, so the tests would check real text.
- The expected card sequences for the adaptive mode were calculated by hand before the tests existed, for example A, B, C, D, B, E, B for the course example, and Q0, Q1, Q2, Q0, Q3 for the default rest of a 10-card deck.
- `RandomMode` had to be tested by properties only (every card once, same seed gives same order, the global random state is not used), and the prompt forbade writing the concrete order of `Random(0)`, because it depends on the implementation of `shuffle`.
- The constraints said: no `# type: ignore`, no `unittest.mock`, no reading of private attributes except in one extensibility test, and if a test fails because of a real bug, do not change the source code and report it.
- The Verification section asked for nine mutations of `quiz_engine.py` (for example `rest + 1`, `<=` instead of `<`, removing the "not twice in a row" condition, `lower()` instead of `casefold()`, removing the `shuffle` call), each restored with `git checkout`, and branch coverage only from the command line.

**AI Response:** Claude Code created 92 new tests, 66 in the modes file and 26 in the session file, and the whole suite had 158 tests, all passing. Coverage of `quiz_engine.py` was 100% for lines (151) and branches (42). The nine mutations all made at least one test fail: 6, 8, 1, 1, 3, 1, 5, 3 and 2 tests respectively. It reported that the weakest check was removing `shuffle`, caught by one test, and that replacing the tuple copy with the original list did not break the random case, because `RandomMode` makes its own copy. The prompt contained two instructions that contradicted each other, a session test "through the factory" and also "with a directly built mode with `rest=2`", and Claude Code resolved it by parametrizing both variants and explained why. It found no bug in `quiz_engine.py`.

**Changes Made:**
- Accepted the tests as generated after reviewing both files against the prompt: the two required names, the sequences, the comments about duplicates and immediate repetition, the single use of the private registry, and the absence of `# type: ignore` and `unittest.mock`
- Recalculated three adaptive sequences by hand and compared them with the tests
- Verified the counts in the pytest output. The summary said the modes file had 92 tests, but the real numbers are 66 and 26, and 92 is the total of both. The suite total of 158 was correct
- Noted that `make_cards` is duplicated in both test files. It was requested by the prompt (no shared module), so I accepted it for now and put it in the list for the final quality phase
- Committed the tests (`b271794`)

**Reasoning:**
- A deliberate change to the code that makes tests fail shows that the tests protect a behavior. The most useful ones here were the off-by-one in the rest, the failure limit and the "no immediate repetition" rule, because those are the decisions of the adaptive mode that are easiest to get wrong
- Testing `RandomMode` by properties avoids a test that would break with no real bug if `shuffle` changed
- The contradiction in my prompt was my mistake, and the AI handled it openly instead of picking silently
- A 100% coverage total includes the test files themselves, so I read the figure for `quiz_engine.py` and not the total

**Outcome:** 158 tests pass. `quiz_engine.py` has 100% line and branch coverage, and `black`, `isort`, `flake8` and `mypy` are clean. All nine mutations were detected and the source file was restored and unchanged. The engine is complete and tested, and the command line interface is the next phase.

**Lessons Learned:**
- Mutation checks tell me more than the coverage percentage. A line can be executed without any test noticing a wrong value
- A summary written by the AI can contain a wrong figure even when the code and the tools are right, so I check it against the real output
- The weakest mutation shows where a test suite is thin, and I can decide whether to reinforce it or accept the limit
- If my prompt contradicts itself, a good agent points it out. I should reread my prompts for contradictions before sending them
- Calculating expected results before the tests exist keeps the review independent from the AI

### 2026-11-19 - Console interface in three prompts (Prompts 3A, 3B and 3C)

**Context:** The data layer and the quiz engine were tested and committed, and the course requires a command line interface with `argparse`, green and red feedback, a clean exit with "exit" or Ctrl+C, and a final summary with total questions, accuracy and missed terms. I split the work into three small prompts that all modify `ui.py`: 3A for the arguments, the question loop and the load errors; 3B for the colors and the ways to quit; 3C for the final summary and the `--stats` flag. Before writing any prompt I agreed the design with a separate Claude chat session.

**AI Tool Used:** Claude Code in VS Code, plus a separate Claude chat session as a planning assistant to draft the prompts and review the results.

**Prompt/Request:** All three prompts followed the Requirements Prompt pattern (Context, Requirements, Constraints, Examples) in English, with a Verification section. Each one said which files must not change and which later parts must not be implemented yet.
- Design decisions fixed in the prompts: questions are labeled `Q1`, `Q2` and so on, and a repeated card shows `Q5 (review)`; after a wrong answer the expected answer is shown; only green and red are used, with raw ANSI codes and no extra options; the exit code is 0 for a normal end or a quit and 1 when the deck cannot be loaded; the short summary is always shown and `--stats` shows the full report instead of repeating the short table.
- Prompt 3A: `build_parser()` with `-f`, `-m` (choices taken from `QuizModeFactory.available_modes()`) and `--stats`, `run()` with injectable `input_fn`, `output_fn` and `error_fn` so that the loop can be tested without a keyboard, a minimal `main.py`, and friendly load errors.
- Prompt 3B: green and red feedback, and one function that handles "exit", Ctrl+C and the end of the input, the only place where `KeyboardInterrupt` and `EOFError` may be caught.
- Prompt 3C: functions that return lists of lines (an ASCII table, the missed terms, the short summary and the full report) so they can be checked without capturing the screen. The expected tables were generated with a script before I wrote the prompt, so the verification compares with exact text.

**AI Response:** In 3A, Claude Code created `ui.py` and replaced `main.py`, and its eight scripted checks matched the expected output, including the adaptive labels `Q5 (review)` and `Q7 (review)` and 24 questions for a deck of 8 cards always answered wrong. In 3B, it kept the single `except (KeyboardInterrupt, EOFError):` and chose a small frozen dataclass `ReadResult` instead of a tuple, explaining why in the docstring. In 3C, it added the four functions I asked for and one more, `_accuracy_text`, to avoid writing the same format twice. Its own check that every table line has the same length failed once because of a bug in its script, which counted the empty lines, and it fixed the script and said so in the report.

**Changes Made:**
- No code changes were needed in any of the three prompts. I accepted each result after reading `ui.py` against the prompt and running the tools, and I committed after each one (`03e8d2d`, `c146b49` and `47fe8ab`)
- Moved the friendly handling of load errors from prompt 3B to 3A, because it was small and the first manual test with a missing file would otherwise show a traceback
- Dropped the extras I had proposed (a `--no-color` flag, a `NO_COLOR` variable and a terminal check), following the rule of not adding what is not requested
- Ran the manual checks that a script cannot do: the colors in PowerShell, `exit`, Ctrl+C, Ctrl+Z followed by Enter, a complete adaptive game, a missing file, a directory, an invalid mode and a broken JSON file
- Traced the adaptive game by hand: 8 cards and 9 questions, one failure and a review at question 8, which gives 88.9%, and it matched the screen

**Reasoning:**
- Passing the input and output functions as parameters keeps `ui.py` testable without patching the keyboard
- Catching Ctrl+C and the end of the input in a single place avoids scattered handlers that are hard to maintain
- Functions that return lines and do not print let the next phase check the text exactly, and keep the printing in one function
- ASCII table borders avoid an encoding error if the output is redirected on Windows
- The word "exit" is reserved, so a card whose correct answer is literally "exit" cannot be answered correctly. I documented this limitation in the code instead of adding a more complex quit command

**Outcome:** The application works end to end: `python main.py --help`, a sequential game, a random game and a complete adaptive game, with colors, a clean exit in three ways, a summary table and the full report with `--stats`. Exit codes are 0 for a normal end or quit, 1 for a deck that cannot be loaded, and 2 for invalid arguments (the default of `argparse`). `black`, `isort`, `flake8` and `mypy` pass, and the 158 existing tests still pass. `ui.py` and `main.py` have no tests of their own yet, which are the next phase.

**Lessons Learned:**
- Features of a real terminal, such as colors, Ctrl+C and Ctrl+Z, can only be checked by hand. A script can call the function but cannot press the keys
- A single catch for the interruptions made them easy to review: I could search the file and see one line
- Deciding the design with exact examples before the prompt, such as the table layout, turned the verification into a comparison with exact text
- Giving the AI freedom on an internal detail, such as a tuple or a dataclass, worked when I asked it to explain the choice in the docstring. My own sentence about it in the prompt was confusing, so I should reread a requirement before sending it
- The agent reported a failure in its own verification script instead of hiding it. That makes its other results easier to trust
- This phase produced no corrected code, so the evidence for reviewing the AI is in the design decisions I made first and in the manual tests


### 2026-11-19 - Tests for the console interface: helpers and test_ui (Prompts 4A and 4B)

**Context:** After the command line interface was finished, `ui.py` and `main.py` had no tests. The coverage report said 88%, but that total included the 617 lines of the test files themselves. Counting only the application code (323 lines), the real figure was about 69%, below the 80% required by the course. I split the work into two prompts: 4A for shared test helpers with their own tests, and 4B for `tests/test_ui.py`. I decided to build the helpers in their own prompt, so that this and the next prompt (integration tests) can reuse them.

**AI Tool Used:** Claude Code in VS Code, plus a separate Claude chat session as a planning assistant to draft the prompts and review the results.

**Prompt/Request:** Both prompts followed the Requirements Prompt pattern (Context, Requirements, Constraints, Examples) in English, with a Verification section.
- Prompt 4A: create `tests/helpers.py` and `tests/test_helpers.py`. The helpers are `make_cards`, `make_pairs`, `write_deck`, `green` and `red`, a `ScriptedInput` that replaces `input()`, a `LineRecorder`, and `run_ui`. Two design rules were in the prompt: the color codes are written as literals and not imported from `ui.py`, so a change of color in `ui.py` is detected, and `ScriptedInput` raises `AssertionError` when it runs out of replies and never simulates an end of input, so a bug that asks for one answer too many cannot pass for a Ctrl+Z.
- Prompt 4B: create `tests/test_ui.py`. I generated the expected tables and outputs with a script before writing the prompt, and put them in the prompt as literal lists. The tests had to compare whole output lists with these literals and never compute an expected value by calling the function under test. The prompt also asked for tests with the real `input` and `print` (using `sys.stdin` replaced by `io.StringIO` and `capsys`) and for `main.py` through `runpy`.
- Both prompts asked for mutation checks: break the code on purpose, confirm that at least one test fails, and restore the file. For 4A, the new file was not committed yet, so the prompt told the agent to restore it from a backup copy and to compare file hashes at the end.

**AI Response:** For 4A, Claude Code created the two files with 24 tests (182 in total) and 100% line and branch coverage for the helpers. All six mutations were detected, for example turning the green code into red, or removing the line that records the prompt. It also checked that the color codes in `helpers.py` were literal escape sequences, because an earlier tool of the same agent had once turned an escape into an invisible character. For 4B, it created 72 tests (254 in total), and `ui.py` and `main.py` reached 100% of lines and branches. All 15 mutations were detected: colors, the comparison of the exit word, the single `except` for Ctrl+C and end of input, the empty line after an interruption, the closing messages, the review label, the percentage format, the missed terms prefix, the incorrect answers row, the order of two report rows, `str.lower` in the parser, the load error exit code and the review rule. It found no bug in `ui.py`.

**Changes Made:**
- Accepted both results as generated after reading the files against the prompts, and committed them (`3d71d6e` and `4b515ef`)
- Recalculated the real coverage of the application code before writing the prompts, and used it to decide that the interface tests were required and not optional
- Kept three tests that compare only the end of the output (the exit word with `--stats`, all answers wrong and all answers correct). The prompt allowed it and the full-output tests cover the rest
- Noted for the quality phase that `make_cards` now exists in three files, and that the two older test files should use the shared helper

**Reasoning:**
- A coverage total that includes the test files rewards writing tests and hides untested application code, so I read the figure for the application files
- If a test builds its expected table by calling `ui.py`, it compares the code with itself and cannot detect a wrong layout. Literal tables written by hand are an independent reference
- In the case of 3 questions with 2 correct answers, the number of incorrect answers and the number of distinct missed cards are both 1, so a swapped row would go unnoticed. I added a case with 7 questions and 4 correct answers, where they are 3 and 1, and the mutation that swapped them failed exactly that test
- A scripted input that fails when it runs out is safer than one that simulates the end of the input, because the second can hide a missing answer in the program
- The two tests that use `io.StringIO` depend on how `input()` writes the prompt when the input is not a terminal. I reasoned about it and warned that I could not run it. The real output matched my expectation

**Outcome:** 254 tests pass. The application code has 100% line and branch coverage, and `black`, `isort`, `flake8` and `mypy` are clean. The shared helpers are ready for the integration tests. The work was done in commits `3d71d6e` (helpers) and `4b515ef` (interface tests).

**Lessons Learned:**
- A coverage percentage can look good because of the tests themselves, so I look at the figure for the application files
- Expected values should come from a source independent from the code under test, such as a script or literal text
- When two numbers are equal by chance, a test cannot tell them apart, so I choose a case where they differ
- Mutation checks keep being the best way to know that tests protect a behavior: 21 deliberate breaks were all caught in these two prompts
- Test helpers also need tests, because a faulty helper makes other tests pass for the wrong reason
- This phase also produced no corrected code. The evidence for reviewing the AI is in the design decisions I took before the prompts and in the checks I made afterwards


### 2026-11-19 - Integration tests with the real decks (Prompt 4C)

**Context:** The modules and the console interface had their own tests, but nothing checked the whole application working together with the two real decks in the `data` folder. The course also requires a test named `test_full_session` that simulates a user answering 3 questions and checks the final statistics. I wrote one prompt for the file `tests/test_integration.py`.

**AI Tool Used:** Claude Code in VS Code, plus a separate Claude chat session as a planning assistant to draft the prompt and review the result.

**Prompt/Request:** One prompt in English, with the Requirements Prompt structure (Context, Requirements, Constraints, Examples) and a Verification section.
- To fix the expected results, I asked for the content of both decks and wrote a script that simulates the rules of the adaptive mode independently from the code. I checked the script against two references before trusting it: the sequence A, B, C, D, B, E, B from the first engine tests, and the game that I had played by hand in the terminal (9 questions, one review at question 8). It reproduced both.
- The prompt gave the decks, the tables and the exact sequences of questions as literal text: 24 questions for the 8-card deck always answered wrong, 20 for the glossary when each card is failed once and then answered correctly, and 30 when it is always wrong. It also asked for a helper that answers by reading the last question shown, so that the random and adaptive modes can be played without knowing the order in advance, and for a test of the real decks that pins their content.
- One test had to run `main.py` in a separate process, with a timeout. The prompt also asked for eight mutations of the engine, the loader and the interface, each restored with `git checkout`.
- The prompt said that if a test failed, the agent had to stop and report, because the cause could be a bug in the code or a mistake in my calculation.

**AI Response:** Claude Code created 19 tests (273 in total), and all passed on the first run, so my sequences matched the real behavior. Coverage of the project was 100% for lines and branches. The eight mutations were all detected: the minimum rest, the failure limit, the mode registry, the rule that a review card must wait for its rest, the key `cards` of the object format, the duplicates in the missed terms, the deck size in the report and the `strip` of the answer. The separate-process test took 0.93 seconds. It said that my message seemed to end in the middle of a sentence, and it interpreted the rest correctly. It also kept the rule of not touching any existing file.

**Changes Made:**
- Accepted the file as generated after reading it against the prompt, and committed it (`73af809`)
- Changed my plan before writing the prompt: I had meant to ask for the property "no card is asked twice in a row" in the adaptive mode. The simulation showed that it is false. When only one card is left, it is repeated in a row, as the rule says "if there is another candidate". The glossary sequences end with card 10 asked twice, and then three times. I replaced the property with exact sequences and a comment that explains the repetition
- Kept the tests of the random mode as properties, plus one test that runs the mode up to 5 times and checks that at least one order differs from the file order. The chance of 5 identical orders is below 1 in 10^30, so it cannot fail by luck, and without it a registry that returned the sequential mode for `random` would pass most other random tests
- Noted that some tables are repeated in `test_ui.py` and `test_integration.py`, and that `make_cards` has three copies, for the quality phase

**Reasoning:**
- A test that fixes a sequence must come from a source independent from the code. A simulation written from the rules, and checked against two known references, gives that source. Copying what the code produces would only compare the code with itself
- If I had asked for the false property, the test would have failed because of my mistake, and I could have taken it for a bug in the engine. Simulating first avoided that
- A real game played by hand makes a good regression test, because it was checked with my own eyes
- Running the program in a separate process checks what the unit tests cannot: that the entry point, the exit code and the standard streams work for real. One test is enough, because it is slower and does not count for coverage
- My prompt contained an unfinished sentence in the requirement about the table of the separate-process test. The agent used the exact lines, so there was no damage, but I should reread my prompts before sending them

**Outcome:** 273 tests pass. The project has 100% line and branch coverage, and `black`, `isort`, `flake8` and `mypy` are clean. The application is tested at three levels: each module alone, the console interface with scripted input, and the whole program with the real decks, including a separate process. The commit is `73af809`.

**Lessons Learned:**
- Simulating the expected behavior independently, and checking the simulation against known cases, catches mistakes in my own reasoning before they reach the tests
- A property that sounds natural, such as "never twice in a row", can be false at the edge. Exact sequences make the edge visible
- A test of randomness can still be deterministic in practice if the probability of a false failure is negligible
- The agent said that my message looked cut off and still did the right thing, which shows the value of clear and complete prompts
- Three levels of tests find different problems. Unit tests find a wrong value, integration tests find a wrong connection, and the separate process finds a wrong entry point
- This phase again produced no corrected code. The evidence of review is in the independent calculation and in the mistake that it prevented












### [Date] - [Brief Description]

**Context:** 

**AI Tool Used:** 

**Prompt/Request:** 

**AI Response:** 

**Changes Made:** 

**Reasoning:** 

**Outcome:** 

**Lessons Learned:** 

---

### [Date] - [Brief Description]

**Context:** 

**AI Tool Used:** 

**Prompt/Request:** 

**AI Response:** 

**Changes Made:** 

**Reasoning:** 

**Outcome:** 

**Lessons Learned:** 

---

## Tips for Effective AI Collaboration

### 1. Be Specific in Your Requests
- ❌ "Write a function"
- ✅ "Write a function that validates email addresses using regex, returns a boolean, and includes proper error handling"

### 2. Provide Context
- Include relevant code snippets
- Explain the larger goal
- Mention any constraints or requirements

### 3. Review and Understand
- Never copy AI code without understanding it
- Ask for explanations of complex logic
- Test the code before accepting it

### 4. Iterate and Refine
- Use follow-up questions to improve the code
- Ask for alternative implementations
- Request code reviews and suggestions

### 5. Document Your Process
- Keep detailed notes in this log
- Explain your decision-making process
- Track what works and what doesn't

## Common AI Collaboration Patterns

### Code Generation
- Initial implementation of classes/functions
- Boilerplate code creation
- Test case generation

### Code Review
- Ask AI to review your code for issues
- Request suggestions for improvements
- Get feedback on code structure

### Problem Solving
- Debugging help
- Algorithm suggestions
- Architecture advice

### Learning and Explanation
- Ask for explanations of complex concepts
- Request examples of design patterns
- Get guidance on best practices

## Reflection Questions

As you work through the project, consider these questions:

1. **What types of tasks did AI help with most effectively?**
2. **Where did you need to make the most modifications to AI suggestions?**
3. **What patterns did you notice in AI strengths and weaknesses?**
4. **How did your prompting technique improve over time?**
5. **What would you do differently in future AI collaborations?**

## Summary Statistics

At the end of your project, fill out these statistics:

- **Total AI interactions:** ___
- **Lines of AI-generated code used:** ___
- **Lines of AI-generated code modified:** ___
- **Most helpful AI interaction:** ___
- **Most challenging AI interaction:** ___
- **Biggest lesson learned:** ___

---

**Note:** This log is a required component of your final project report. Be thorough and honest in your documentation to demonstrate your learning process and AI collaboration skills.