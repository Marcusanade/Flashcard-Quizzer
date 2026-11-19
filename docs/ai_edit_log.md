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


### 2026-11-19 - Statistics report redesign (Prompts 5A and 5B)

**Context:** The final statistics were a plain two column table with the missed terms listed below it. I wanted a more elegant report: a box of fixed width, an accuracy bar and a rank letter, with the missed terms inside the box and wrapped when they are long. The design had to stay ASCII only, because Unicode box characters can fail when the output is redirected on Windows. This change affected about 35 tests that compared the old table, so I did it before adding other features, to avoid writing new tests with the old format and rewriting them later. I split the work into two prompts: 5A for `ui.py` and `tests/test_ui.py`, and 5B for the integration tests, with a single commit at the end.

**AI Tool Used:** Claude Code in VS Code, plus a separate Claude chat session as a planning assistant to design the layout, generate the expected output and draft the prompts.

**Prompt/Request:** Both prompts followed the Requirements Prompt pattern (Context, Requirements, Constraints, Examples) in English, with a Verification section.
- Design agreed before any prompt, with a preview: a 60 column box with a centered title, the rows total questions, accuracy and rank, a 20 cell bar, and ranks S (100%), A (90% or more), B (75%), C (60%) and D, with "-" when there are no questions. The bar and the rank use integer arithmetic only, so a value at a threshold cannot cross it because of a floating point rounding. Long deck paths are shortened keeping their end.
- Prompt 5A: change the report functions in `ui.py` and update `tests/test_ui.py`. I generated the expected blocks with a script that implements the design separately and put them in the prompt as literal text. The prompt predicted that exactly 16 tests of `tests/test_integration.py` would fail afterwards and that three would still pass. It asked for 15 mutations, with a backup copy of `ui.py` and a hash comparison, because that file had changes that were not committed yet.
- Prompt 5B: adapt the integration tests. Instead of writing 25 more literal blocks, I asked for a reader of the box in `tests/helpers.py` (`parse_report`) that does not import anything from `ui`, with its own tests and literal boxes, so the integration tests check the numbers and the missed terms of real games while the exact layout stays pinned in `test_ui.py`. It asked for 14 mutations of the engine, the loader, the interface and the reader itself.

**AI Response:** In 5A, Claude Code rewrote the report functions, removed the old ones and updated the tests. `ui.py` reached 100% line and branch coverage with `test_ui.py` alone, and all 15 mutations were detected. The suite then had 308 passing tests and exactly the 16 failures that I had predicted, with the names I expected. It reported two small deviations: a helper `_head_lines` that I had not listed, and a different way of slicing in `_fit`, which avoids a case where `text[-0:]` would return the whole text. In 5B it fixed the 16 tests, added `parse_report` and its tests, and the suite reached 340 tests with 100% line and branch coverage. Of the 14 mutations, one was not detected with the tests that I had listed: changing the label width from 19 to 18 characters, because the real labels have at most 17 characters. It said so openly and added a test with a label of 19 characters, which detects it. It also added a case that I had not listed, a term after the "none" row, because otherwise another mutation gave the same result.

**Changes Made:**
- Changed the order of the work before writing code: statistics first, so the tests of the next features start with the new format
- Predicted by reading the integration tests that exactly 16 would fail and 3 would pass, and used that count as a check that nothing else was affected. It matched
- Accepted the two deviations of the agent after reading them: the helper `_head_lines` and the safer slicing in `_fit`
- Accepted the two extra tests that the agent added after the mutations. Both fix gaps in my list of tests for the reader, not in its code
- Committed all the files together once the whole suite was green (`7cb8662`)

**Reasoning:**
- The expected blocks came from a script and not from the code under test, so a wrong layout cannot pass by being compared with itself. Previewing the output also caught a mistake of my own script before it reached the prompt: a label that filled its whole column and was glued to its value
- Integer arithmetic makes the thresholds exact and testable at the boundaries, for example 9 correct of 10 is an A and 89 of 100 is a B
- The reader of the box is a test helper that checks the output from the outside. Because a faulty helper makes other tests pass for the wrong reason, I asked for its own tests and for mutations of the reader itself
- Leaving the suite red between the two prompts was a deliberate step, and nothing was committed until it was green again, so the history has no commit with failing tests
- The reader joins the wrapped lines of a term with one space. This is exact when the wrap happens at a space, as in the real decks, and it is a known limitation

**Outcome:** The report is now a 60 column ASCII box, with an accuracy bar, a rank and the missed terms inside, in a short version and a full version with `--stats`. 340 tests pass, `ui.py` and all the other files have 100% line and branch coverage, and `black`, `isort`, `flake8` and `mypy` are clean. The commit is `7cb8662`.

**Lessons Learned:**
- Predicting which tests will fail before a deliberate change turns the result into a check: the exact count and names matched, so no other behavior moved
- Mutation checks also test my own prompts. Two behaviors were missing from my list of tests, and a mutation that survives shows exactly where
- A test can pass for all real data and still not protect a rule. The label width was the same for every real label, so only an artificial label could tell 18 from 19
- Expected output generated separately and viewed before use catches mistakes in the plan, not only in the code
- This work again produced no wrong code from the AI. The evidence of review is in the predicted failures, the gaps that the mutations found in my own prompt, and the two deviations that I read and accepted


### 2026-11-19 - The --limit option as a rule of the session (Prompt 5C)

**Context:** I wanted an option to stop a quiz after N answered questions, useful for the large decks (for example, 10 random questions from a deck of many). The design question was where the rule belongs. A quiz mode decides which card is next, and the end of the session is a different concern, so I made the limit a rule of the session and not of a mode. That way it works with the three modes, and the console interface does not need to know which mode is running.

**AI Tool Used:** Claude Code in VS Code, plus a separate Claude chat session as a planning assistant to design the rule, calculate the expected results and draft the prompt.

**Prompt/Request:** One prompt in English, with the Requirements Prompt structure (Context, Requirements, Constraints, Examples) and a Verification section. It limited the changes to `quiz_engine.py`, `ui.py` and a new test file, and required that the 340 existing tests pass unchanged.
- Rules fixed in the prompt: the limit counts answered questions, repetitions of the adaptive mode included; a question that was shown and not answered does not count; when the limit is reached the quiz ends as a normal end (`Quiz finished.`) with no extra message; a deck shorter than the limit ends when the cards run out; the adaptive mode ends at the limit even if reviews are pending; and `--limit` rejects zero, negative values and non-integers with exit code 2.
- One decision that I wrote explicitly: when the limit is reached, `next_question()` returns `None` **without asking the mode for a card**, because a mode with state, such as the adaptive mode, would advance for a card that nobody sees. The check of an unanswered pending question had to stay first, to keep the existing contract.
- The tests had to use a `CountingMode` that counts every call to `next_card`, so the rule can be checked directly. The expected sequences came from my independent simulation of the adaptive mode, for example A, B, C, A (review), B (review) for three cards always answered wrong with a limit of 5.
- Because the code did not exist yet, I described the eight mutations by behavior (one question too many, checking the limit after asking the mode, counting when asked instead of when answered, accepting zero, and so on) and asked for backups of `quiz_engine.py` and `ui.py`, which had uncommitted changes.

**AI Response:** Claude Code added the `max_questions` parameter to `QuizSession` with its validation, put the limit check after the pending-question check and before the call to the mode, and added `--limit` with a `_positive_int` function. It created 28 tests, and the suite reached 368 tests with 100% line and branch coverage. All eight mutations were detected. Its result for the "accept zero" mutation was 5 failing tests, which is more than the single test that I had predicted. It also defined its own `summary` and `assert_game` helpers in the new test file instead of importing the ones from the integration tests, to avoid coupling the two files.

**Changes Made:**
- Accepted the code after reading the whole diff: the order in `next_question`, the exact error message, the creation of the session inside the existing `try` block, and no change to the closing line or to the report
- Investigated the difference in the "accept zero" mutation. The agent had written `_positive_int` with one rejection point: a text that is not an integer is converted to `0`, and the check `value < 1` rejects it. So lowering the minimum also lets `abc`, `2.5` and the empty text through. My prediction assumed two separate checks. The report was correct and my prediction was wrong
- Noted that the helpers `summary_values` and `assert_ends_with_report` now exist in three places, and put their move to `tests/helpers.py` in the quality phase
- Committed the three files (`4cf7bea`)

**Reasoning:**
- A limit that is a rule of the session works with every mode, and the modes stay responsible for choosing cards only. This is the same separation as the Strategy pattern of the engine
- Returning `None` before asking the mode avoids a hidden side effect. The `CountingMode` makes the test fail if the check is moved after the call
- Counting answered questions is consistent with the statistics and with the way `exit` works, so the number in the report always matches the number of answers
- Predicting the result of a mutation only makes sense if I know the structure of the code. For code that does not exist yet, describing the mutations by behavior and reading the report afterwards is the honest way

**Outcome:** `--limit N` works with the three modes: for example, `python main.py -m random --limit 3 -f data/glossary.json` asks three random cards and then shows the report. The real sessions matched my calculations, including the adaptive mode with a limit of 5 (three questions and two reviews). 368 tests pass, with 100% line and branch coverage in every file, and `black`, `isort`, `flake8` and `mypy` are clean. The commit is `4cf7bea`.

**Lessons Learned:**
- Deciding where a rule belongs, in the session or in a mode, before writing the prompt kept the change small: 51 lines in the source
- A rule that must not have a side effect needs a test that observes the side effect, such as a mode that counts its calls
- A wrong prediction of mine was explained by reading the code afterwards. The check of an AI report is useful in both directions, and the report was the correct one here
- Asking for backups before mutating files with uncommitted changes avoided losing work, as in the previous phases
- This feature again needed no correction of the AI code. The evidence of review is in the design decision, in the test that observes the side effect and in the investigation of a result that did not match my expectation


### 2026-11-19 - Sound feedback with the terminal bell (Prompts 5D and 5E)

**Context:** I wanted an optional sound after each answer, in the style of old arcade games: a short sound for a correct answer and a different one for an incorrect answer. The first ideas (a sound of uncertainty while typing, and different tones for each platform) were too complex, so I chose the simplest portable option: the terminal bell, with one ring for a correct answer and three for an incorrect one. I split the work into two prompts: 5D for a new sound module and 5E to connect it to the console interface with a `--sound` option.

**AI Tool Used:** Claude Code in VS Code, plus a separate Claude chat session as a planning assistant to research the options, design the module and draft the prompts.

**Prompt/Request:** Both prompts followed the Requirements Prompt pattern (Context, Requirements, Constraints, Examples) in English, with a Verification section.
- Design agreed before the prompts. I checked the documentation of `winsound`, and tested on my own machine that the bell is audible in the VS Code terminal, which needed the setting `accessibility.signals.terminalBell` with `"sound": "on"`. The design used the Strategy pattern: an abstract `SoundPlayer`, a `SilentPlayer` that does nothing and acts as a null object (so the interface needs no `if` to know whether sound is enabled), and a `BellPlayer`. I chose a plain function `create_player` and not a factory class, because with two options a registry would have forced the pattern. The bell goes to the standard error stream, so a redirected output file does not fill with control characters.
- Prompt 5D: create only `sound.py` and `tests/test_sound.py`, with the writing and the waiting injectable so the tests make no noise and do not wait. Sound must never break a quiz, so write errors are ignored. I added one decision of my own: a Ctrl+C that arrives during the 0.42 seconds of the failure sound only cuts the sound, because a second place that catches `KeyboardInterrupt` would break the rule that it is handled in only one function. The prompt asked for 12 mutations, with a backup of the new file because it was not committed.
- Prompt 5E: add `--sound` and connect the player. The player is an optional last parameter of `run()` and `_ask_questions`, so the 388 existing tests did not change, and an injected player wins over the flag. The sound plays right after the feedback line, and never when the user quits. A shared timeline between the output and a recording player checks the order. One test runs the program in a separate process and checks that the bell goes to the standard error. The prompt forbade running the program with `--sound` in the terminal, so nothing would ring while the agent worked.

**AI Response:** In 5D, Claude Code created both files and the suite reached 388 tests with 100% line and branch coverage. All 12 mutations were detected, though one in a different way: removing the handling of `KeyboardInterrupt` made the exception rise out of the test and abort the whole pytest session, and the agent noticed that its script showed "0 failures" and repeated the mutation by hand to confirm it. It made two small adjustments to my prompt: a helper `returned(...)`, because mypy rejects using the value returned by a method that returns `None`, and a list that must stay empty instead of a helper that fails the test when `time.sleep` is called, because the failing line would never run and would break the 100% coverage. In 5E it connected the player, and the suite reached 408 tests with 100% coverage. All 9 mutations were detected. It reported one deviation: in the tests of the real bell, the deck of three cards with two scripted answers made the program ask a third question, so it added `--limit 2`, and the expected values stayed the same.

**Changes Made:**
- Accepted both results after reading the code of `sound.py` and the diff of `ui.py` and `tests/helpers.py` against the prompts, and after checking that the tests contain no `# type: ignore`, no `unittest`, no `mock` and no `print`
- Accepted the two adjustments of 5D and the `--limit 2` deviation of 5E
- Noticed in the diff that the new line `player = ...` in `_ask_questions` sits between the comment about identical cards and the line `asked`, which the comment explains. It is cosmetic, so I put it in the list for the quality phase
- Noticed that the summary of 5D said "33 cases" for the sound tests, while pytest collected 20 items and the suite grew from 368 to 388. The count in the summary was wrong, as in two previous summaries
- Played the real program with `--sound` in the VS Code terminal. The two sounds were the same and a little late. I did not change the code and kept the bell

**Reasoning:**
- A null object removes a check from every call, and it is the reason that the rest of the program is unchanged without `--sound`
- The bell cannot change its pitch or its length, so the failure sound is made of three rings with silences between them
- Reading `sys.stderr` and `time.sleep` when they are used and not when the module is imported lets the tests replace them. Without that, the tests would wait for real
- Banning the real program with `--sound` in the agent run, and replacing `time.sleep` in the tests that use the real bell, keeps the test runs silent
- The listening test showed what the tests could not. The program does send one ring for a correct answer and three for an incorrect one, and a test checks it on the standard error stream, but the terminal decides what to do with those rings. Some terminals limit the number of bells per second, for example Windows Terminal, and the VS Code accessibility sound is a fixed sound that can be late. In my environment the two answers sounded the same. The alternative of real tones with `winsound.Beep` would be immediate and different for each answer, but it only works on Windows. I had chosen the portable option for simplicity, and after listening I decided to keep it, and to document that the sound depends on the terminal

**Outcome:** `--sound` is available and off by default. 408 tests pass, with 100% line and branch coverage in every file, and `black`, `isort`, `flake8` and `mypy` are clean. The commits are `5d88f2f` (the sound module) and `c9caa34` (the connection with the interface). The sound is a small extra and works as designed, but in my terminal it cannot tell a correct answer from an incorrect one by ear, and I will say so in the README and in the report.

**Lessons Learned:**
- Some behavior cannot be tested by a program. The tests prove what the program sends, and only a person listening can prove what the terminal does with it
- A choice made for simplicity can show its limits with real use. Keeping a simple solution with its limits documented is a valid decision
- Splitting a feature into a module and a connection made each step small and easy to review, and let me commit the module before the interface used it
- The agent checked a result that looked wrong in its own script (a mutation that aborted the session instead of failing a test), instead of accepting "0 failures"
- Summaries of the AI can contain a wrong count even when the code is right, so I check them against the real output
- This feature again needed no correction of the AI code. The evidence of review is in the design decisions, in the mutation that aborted the session, in the two adjustments that I read and accepted, and in the honest result of the listening test


### 2026-11-19 - Intro banner and the periodic table deck (Prompts 5F and 5G)

**Context:** The last two additions of the extra features phase. The first was an intro banner in the style of the old arcade games, shown when the program starts. The second was a deck of my own for the project, as the submission asks for my own decks in `data/`: the periodic table, with two questions for each of the 118 elements, which is a good use of the `--limit` option because a full game would have 236 questions.

**AI Tool Used:** Claude Code in VS Code, plus a separate Claude chat session as a planning assistant to research ideas, design the banner, verify the data of the elements and draft the prompts.

**Prompt/Request:** Both prompts followed the Requirements Prompt pattern (Context, Requirements, Constraints, Examples) in English, with a Verification section.
- Banner. I asked the planning assistant to search for ideas to make it look better. The search gave general guidelines (blocky capital letters, a green phosphor look, ASCII that works in every terminal, a width that does not wrap) and the assistant discarded Unicode block characters, which can fail with redirected output on Windows. I tried a drop shadow on the letters and rejected it, because with letters of only five rows it looked blurry. The design is a 60 column box in the same style as the final report, with the frame in green, the big letters in dark yellow, which was my choice, and a status line that changes with each game (mode and number of cards). The prompt put the art in a data module and generated it with a script, and it defined the exact color format of each kind of line. The banner is a parameter of `run()` that is off by default and only `main.py` turns on, so the existing tests of `run()` did not change. It must not appear with `--help` or when the deck cannot be loaded.
- Deck. Before writing the prompt, the assistant verified the 118 elements against a table that uses the IUPAC spelling, and confirmed the names of the four newest elements in a separate source. It then typed its own lists of symbols and names from memory and compared them with the source: no differences. It also checked that the numbers go from 1 to 118, that the symbols and names are unique, and that the longest question has 45 characters, so it never wraps in the report. The first idea had been two decks, one for symbols and one for atomic numbers, because of a mode that was later discarded. I decided on a single file, and the assistant agreed that the reason had disappeared. The prompt asked Claude Code to generate the file with a throwaway script, and the tests had to hold the table as a literal typed again, a second small literal of 24 known elements typed independently, structural tests that do not use either table, and real games through the interface.
- Both prompts asked for mutations (13 for the banner, on the code, and 9 for the deck, on the data) with backups and hash checks for the files that were not committed.

**AI Response:** For the banner, Claude Code created the data module, the two functions that build the colored lines, the parameter of `run()` and the change of `main.py`. The suite reached 431 tests with 100% line and branch coverage, and all 13 mutations were detected, including showing the banner before the deck is loaded and leaving the yellow color without its closing code. For the deck, it generated the file with a script that it deleted, created 38 tests and reached 469 tests with 100% coverage. Eight of the nine mutations were detected at once. The ninth, a space added at the end of the answer for gold, was not, and the agent explained why: the loader strips the texts, so the space was gone before the test saw it. It changed that test to read the raw JSON file, with a comment, and the mutation was detected.

**Changes Made:**
- Accepted the banner after reading the code and the diff against the prompt, and after looking at it in my own terminal: the frame in green and the letters in dark yellow looked right
- Accepted the deck after playing it with `python main.py -f data/periodic_table.json -m random --limit 10`: the questions were short, clear and had a single answer
- Accepted the change that the agent made to the test of outer spaces. It fixes a gap in my specification, because I asked to check the loaded cards, which the loader already cleans
- Put a cosmetic detail for the quality phase: the banner condition is written `if banner is True` and not `if banner:`
- Committed the banner as `8560731`

**Reasoning:**
- Making the banner a parameter that is off by default kept 408 tests unchanged, and the one test that needed a change (the separate process) was made less fragile by locating the report from the closing line
- Defining the exact escape codes of each kind of line in the prompt turned the colors into something that a test can compare with a literal, instead of something that only a person can judge
- Verifying data with an independent source, and with two lists typed separately, is cheap and prevents a wrong fact from becoming a wrong test. Three copies of the table typed on their own are a cross-check: a transcription error would leave at least one of them different
- Structural tests that do not use the table catch an error even if the prompt and the file shared the same mistake, for example a repeated symbol
- A test that goes through a filter cannot detect what the filter removes. Reading the raw file is the way to test the file and not the loader
- The default rest of the adaptive mode grows with the deck: for 236 cards it is 10 questions, so a game of 5 questions shows no reviews. A test of the new deck documents this, which was a decision of an earlier phase

**Outcome:** The program starts with a banner in green and yellow with the mode and the number of cards of the loaded deck, and there is a new deck with 236 cards. 469 tests pass, with 100% line and branch coverage in every file, and `black`, `isort`, `flake8` and `mypy` are clean. The banner is in commit `8560731`.

**Lessons Learned:**
- Mutation checks keep revealing gaps in my own prompts. In this phase two behaviors were missing from my lists of tests, and the mutations that survived showed exactly where
- Data deserves the same care as code: a source, an independent cross-check and tests of the structure
- A feature that is off by default and turned on at the entry point can be added without changing the existing tests
- Some qualities can only be judged by a person, such as how a banner looks. I define what can be compared (the codes, the layout) and then look at the result myself
- Nothing in these two prompts needed a correction of the AI code. The evidence of review is in the independent verification of the data, in the gap that a mutation found in my specification, and in the details that I read and accepted










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