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