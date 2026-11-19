# AI-Assisted Development Project Report

**Student Name:** Marc Pascual Val  
**Project Title:** Flashcard Quizzer, a command-line quiz application  
**Date:** 19 November 2026

## Executive Summary

I built a command-line application that loads flashcards from a JSON file and quizzes the user in three modes: sequential, random and adaptive, where missed cards come back later. It gives colored feedback and a final report.

Beyond the specification I added a report with an accuracy bar and a rank, `--limit`, `--sound`, an arcade-style intro and a periodic table deck.

I wrote no code by hand. Claude Code produced everything from 34 small prompts that I reviewed one by one, with a separate Claude chat as planning assistant. There are 482 tests and 100 percent coverage.

## Project Overview

### Problem Statement
New hires need to memorize acronyms. The tool had to run in the terminal, read JSON, offer different quiz modes and have clean, extensible code.

### Solution Approach
The code is modular: a loader validates decks, a quiz engine with no input or output chooses questions and computes statistics, and a console interface talks to the user. The engine uses the Strategy and Factory patterns. Only the standard library is used, on Python 3.10 or higher.

### Final Features
- [x] Loading and validation of two JSON formats, with friendly error messages
- [x] Sequential, random and adaptive modes
- [x] Green and red feedback, and a clean exit with `exit` or Ctrl+C
- [x] Final report with total questions, accuracy and missed terms, and `--stats`
- [x] Extras: accuracy bar and rank, `--limit`, `--sound`, intro banner and periodic table deck

## AI Collaboration Experience

### AI Tools Used
- [x] Claude: Claude Code in VS Code wrote all the code and tests. A separate Claude chat was my planning assistant: it designed each step, wrote the prompts, reviewed the results and drafted the log, but it could not see my disk.
- [ ] GitHub Copilot
- [ ] ChatGPT

### Collaboration Workflow
1. I wrote each prompt in English with Context, Requirements, Constraints and Examples. The prompts were small, and they included exact error messages and expected values calculated by an independent simulation.
2. I asked the AI for code, tests, audits and refactorings.
3. I reviewed every result with a checklist and the quality tools, read the diffs, ran temporary code changes (mutations) to prove that the tests can fail, and played the program myself.
4. When something was wrong I reformulated the prompt and never edited the code by hand. A failing test had to be reported, not silenced.

### Most Valuable AI Interactions

#### Example 1: Tests of the quiz engine
**Context:** The Strategy and Factory engine needed tests.
**AI Prompt:** Sequences that I calculated by hand, and nine mutations to apply and restore.
**AI Response:** 92 tests with full coverage, and all nine mutations were detected.
**Your Changes:** None. One mutation was caught by a single test.
**Outcome:** I used this technique in every later prompt.

#### Example 2: A docstring that promised too much
**Context:** Reviewing the answer checker.
**AI Prompt:** None. My review found that the docstring said an empty answer is incorrect, but the code returned True for two empty strings.
**AI Response:** After my correction prompt, the function rejects empty answers.
**Your Changes:** The prompt asked to change nothing else and to print the results with `repr()`.
**Outcome:** It was the only real correction of AI code in the project.

#### Example 3: Redesign of the report
**Context:** I wanted a more elegant report.
**AI Prompt:** Expected output from a separate script, and my prediction that exactly 16 tests would fail.
**AI Response:** The report passed, and so did my prediction.
**Your Changes:** For integration I asked for an independent reader of the box instead of 25 literals.
**Outcome:** Its mutations exposed two cases missing from my own tests.

### Challenges with AI Collaboration
- Its summaries sometimes had wrong numbers: 92 tests for a file with 66, and 33 cases when pytest collected 20. I compare them with the real output.
- It cannot judge physical results such as the sound or the colors.
- A tool turned an escape sequence into a literal character, and isort caught it.
- Most changes were to my own specifications, not to its code. Three times a mutation showed a case missing from my lists.

## Software Engineering Practices

### Code Quality Measures
- [x] Formatting with Black and isort
- [x] Linting with flake8 and mypy, with type hints required on every function
- [x] Type hints everywhere
- [x] Docstrings: an audit found none missing in 67 functions and 14 classes of the application
- [x] Error handling: bad decks give one readable line

### Testing Strategy
There are 482 pytest tests: unit tests per module, interface tests with injected input and output, integration tests with the real decks, and one in a separate process. Coverage is 100 percent of 446 statements and 118 branches, with a minimum of 90 percent enforced. I made more than 100 temporary mutations to check the tests, and GitHub Actions runs them on Python 3.10, 3.12 and 3.14. I did not use test-driven development: tests followed each module.

### Design Patterns Used
- **Strategy:** sequential, random and adaptive are different algorithms for the same task, choosing the next card. Each is a subclass of `QuizMode`, and `QuizSession` uses whichever it receives, so the interface never asks which mode it is. A new mode is one class.
- **Factory:** `QuizModeFactory` returns a new mode from the name on the command line. A new mode is one entry in its registry.
- **Strategy with a null object:** the sound players. The silent one removes any `if` from the interface. I did not use a factory class for only two options.

### Code Structure and Organization
The engine knows nothing about the screen, and the interface has no quiz logic. The `--limit` option is a rule of the session and not a mode, because it decides when to stop. In the final cleanup I moved repeated test helpers into one module, and no test was lost.

## Technical Challenges and Solutions

### Challenge 1: Adaptive mode and identical cards
**Problem:** Two cards with the same text must not share a failure counter.
**Solution:** Cards are identified by position, and a test uses identical cards.
**AI Involvement:** It implemented my rules. My independent simulation refuted a test property that I had planned, that no card repeats immediately.
**Lessons Learned:** Expected values calculated apart catch my own errors.

### Challenge 2: A sound that tests could not judge
**Problem:** The bell sounded the same for correct and incorrect answers in my terminal.
**Solution:** I kept the portable bell and documented the limit.
**AI Involvement:** The code was right, but only listening showed the problem.
**Lessons Learned:** Tests prove what the program sends, not what a terminal does.

## Code Quality Analysis

### Metrics
- Lines of code: 7,092 of Python, 1,475 in the application and 5,617 in tests
- Test coverage: 100 percent
- Functions and classes: 67 and 14 in the application
- Linting: black, isort, flake8 and mypy report no issues

### Self-Assessment
- **Code Readability:** 4. Small documented functions, but `ui.py` is large.
- **Code Maintainability:** 4. Strategy and Factory make extension easy.
- **Test Quality:** 5. Independent expected values, checked by mutations.
- **Documentation:** 4. README, log and docstrings.

## Learning Outcomes

### Technical Skills Developed
Strategy and Factory patterns, input injection for testing, branch coverage and continuous integration.

### AI Collaboration Skills
Small prompts with exact messages work best. I verify with real output, and I rely on the AI for generation and mechanical refactors but not for design decisions or physical results.

### Software Engineering Insights
A test protects only if it can fail. My first coverage figure included the tests themselves (2,472 statements); the honest one is 446.

## Reflection

### What Worked Well
Small prompts with verification, independent expected values and mutation checks. I am proudest of the engine and the tests that pin it.

### What Could Be Improved
I would write test lists with mutations in mind, test physical results earlier and set up continuous integration sooner. `ui.py` could be split.

### Future Enhancements
A spaced repetition mode as a new Strategy, a history of missed cards, result export and real tones on Windows.

## Conclusion

AI-assisted development worked because every step was small and checked. The AI code needed one real correction and my specifications needed many more, so the review made the result reliable.

## Appendices

### Appendix A: AI Interaction Log
`docs/ai_edit_log.md` has 14 entries. Key ones: 5 (the correction), 10 (the report) and 12 (the sound).

### Appendix B: Code Statistics
`docs/coverage_report.txt` and GitHub Actions.

### Appendix C: Additional Resources
The Python documentation, the IUPAC periodic table and the VS Code settings.
