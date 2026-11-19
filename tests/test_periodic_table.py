"""Tests for the periodic table deck ``data/periodic_table.json``.

The data is written here as literals, typed independently of the script that
generated the deck. There are tests of the content, of the structure and real
games through the console interface.
"""

import json
import re
from pathlib import Path

import pytest

from data_loader import load_flashcards
from models import Flashcard
from tests.helpers import ParsedReport, green, parse_report, red, run_ui

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DECK = DATA_DIR / "periodic_table.json"

ACC_FULL = "[####################] 100.0%"
ACC_ZERO = "[--------------------]   0.0%"

SYMBOL_PATTERN = r"^What is the chemical symbol of (.+)\?$"
NUMBER_PATTERN = r"^What is the atomic number of (.+)\?$"

ELEMENTS = (
    (1, "H", "Hydrogen"),
    (2, "He", "Helium"),
    (3, "Li", "Lithium"),
    (4, "Be", "Beryllium"),
    (5, "B", "Boron"),
    (6, "C", "Carbon"),
    (7, "N", "Nitrogen"),
    (8, "O", "Oxygen"),
    (9, "F", "Fluorine"),
    (10, "Ne", "Neon"),
    (11, "Na", "Sodium"),
    (12, "Mg", "Magnesium"),
    (13, "Al", "Aluminium"),
    (14, "Si", "Silicon"),
    (15, "P", "Phosphorus"),
    (16, "S", "Sulfur"),
    (17, "Cl", "Chlorine"),
    (18, "Ar", "Argon"),
    (19, "K", "Potassium"),
    (20, "Ca", "Calcium"),
    (21, "Sc", "Scandium"),
    (22, "Ti", "Titanium"),
    (23, "V", "Vanadium"),
    (24, "Cr", "Chromium"),
    (25, "Mn", "Manganese"),
    (26, "Fe", "Iron"),
    (27, "Co", "Cobalt"),
    (28, "Ni", "Nickel"),
    (29, "Cu", "Copper"),
    (30, "Zn", "Zinc"),
    (31, "Ga", "Gallium"),
    (32, "Ge", "Germanium"),
    (33, "As", "Arsenic"),
    (34, "Se", "Selenium"),
    (35, "Br", "Bromine"),
    (36, "Kr", "Krypton"),
    (37, "Rb", "Rubidium"),
    (38, "Sr", "Strontium"),
    (39, "Y", "Yttrium"),
    (40, "Zr", "Zirconium"),
    (41, "Nb", "Niobium"),
    (42, "Mo", "Molybdenum"),
    (43, "Tc", "Technetium"),
    (44, "Ru", "Ruthenium"),
    (45, "Rh", "Rhodium"),
    (46, "Pd", "Palladium"),
    (47, "Ag", "Silver"),
    (48, "Cd", "Cadmium"),
    (49, "In", "Indium"),
    (50, "Sn", "Tin"),
    (51, "Sb", "Antimony"),
    (52, "Te", "Tellurium"),
    (53, "I", "Iodine"),
    (54, "Xe", "Xenon"),
    (55, "Cs", "Caesium"),
    (56, "Ba", "Barium"),
    (57, "La", "Lanthanum"),
    (58, "Ce", "Cerium"),
    (59, "Pr", "Praseodymium"),
    (60, "Nd", "Neodymium"),
    (61, "Pm", "Promethium"),
    (62, "Sm", "Samarium"),
    (63, "Eu", "Europium"),
    (64, "Gd", "Gadolinium"),
    (65, "Tb", "Terbium"),
    (66, "Dy", "Dysprosium"),
    (67, "Ho", "Holmium"),
    (68, "Er", "Erbium"),
    (69, "Tm", "Thulium"),
    (70, "Yb", "Ytterbium"),
    (71, "Lu", "Lutetium"),
    (72, "Hf", "Hafnium"),
    (73, "Ta", "Tantalum"),
    (74, "W", "Tungsten"),
    (75, "Re", "Rhenium"),
    (76, "Os", "Osmium"),
    (77, "Ir", "Iridium"),
    (78, "Pt", "Platinum"),
    (79, "Au", "Gold"),
    (80, "Hg", "Mercury"),
    (81, "Tl", "Thallium"),
    (82, "Pb", "Lead"),
    (83, "Bi", "Bismuth"),
    (84, "Po", "Polonium"),
    (85, "At", "Astatine"),
    (86, "Rn", "Radon"),
    (87, "Fr", "Francium"),
    (88, "Ra", "Radium"),
    (89, "Ac", "Actinium"),
    (90, "Th", "Thorium"),
    (91, "Pa", "Protactinium"),
    (92, "U", "Uranium"),
    (93, "Np", "Neptunium"),
    (94, "Pu", "Plutonium"),
    (95, "Am", "Americium"),
    (96, "Cm", "Curium"),
    (97, "Bk", "Berkelium"),
    (98, "Cf", "Californium"),
    (99, "Es", "Einsteinium"),
    (100, "Fm", "Fermium"),
    (101, "Md", "Mendelevium"),
    (102, "No", "Nobelium"),
    (103, "Lr", "Lawrencium"),
    (104, "Rf", "Rutherfordium"),
    (105, "Db", "Dubnium"),
    (106, "Sg", "Seaborgium"),
    (107, "Bh", "Bohrium"),
    (108, "Hs", "Hassium"),
    (109, "Mt", "Meitnerium"),
    (110, "Ds", "Darmstadtium"),
    (111, "Rg", "Roentgenium"),
    (112, "Cn", "Copernicium"),
    (113, "Nh", "Nihonium"),
    (114, "Fl", "Flerovium"),
    (115, "Mc", "Moscovium"),
    (116, "Lv", "Livermorium"),
    (117, "Ts", "Tennessine"),
    (118, "Og", "Oganesson"),
)

# A separate, small literal typed independently of ELEMENTS.
KNOWN = (
    ("Hydrogen", "H", "1"),
    ("Helium", "He", "2"),
    ("Carbon", "C", "6"),
    ("Nitrogen", "N", "7"),
    ("Oxygen", "O", "8"),
    ("Neon", "Ne", "10"),
    ("Sodium", "Na", "11"),
    ("Magnesium", "Mg", "12"),
    ("Aluminium", "Al", "13"),
    ("Silicon", "Si", "14"),
    ("Sulfur", "S", "16"),
    ("Chlorine", "Cl", "17"),
    ("Potassium", "K", "19"),
    ("Calcium", "Ca", "20"),
    ("Iron", "Fe", "26"),
    ("Copper", "Cu", "29"),
    ("Silver", "Ag", "47"),
    ("Gold", "Au", "79"),
    ("Mercury", "Hg", "80"),
    ("Lead", "Pb", "82"),
    ("Nihonium", "Nh", "113"),
    ("Moscovium", "Mc", "115"),
    ("Tennessine", "Ts", "117"),
    ("Oganesson", "Og", "118"),
)


def expected_cards() -> list[Flashcard]:
    """Build the expected cards from ELEMENTS: symbol card, then number card."""
    cards: list[Flashcard] = []
    for number, symbol, name in ELEMENTS:
        cards.append(Flashcard(f"What is the chemical symbol of {name}?", symbol))
        cards.append(Flashcard(f"What is the atomic number of {name}?", str(number)))
    return cards


def name_in(pattern: str, front: str) -> str:
    """Return the element name of a question, failing if it does not match."""
    match = re.match(pattern, front)
    assert match is not None, f"Unexpected question: {front!r}"
    return match.group(1)


# --- Content -----------------------------------------------------------------


def test_deck_loads_with_236_cards() -> None:
    cards = load_flashcards(DECK)

    assert len(cards) == 236


def test_deck_matches_the_verified_table() -> None:
    cards = load_flashcards(DECK)

    assert cards == expected_cards()


@pytest.mark.parametrize(
    ("name", "symbol", "number"), KNOWN, ids=[row[0] for row in KNOWN]
)
def test_known_elements_have_the_right_cards(
    name: str, symbol: str, number: str
) -> None:
    # The IUPAC spelling is used (Aluminium, Caesium, Sulfur).
    backs = {card.front: card.back for card in load_flashcards(DECK)}

    assert backs[f"What is the chemical symbol of {name}?"] == symbol
    assert backs[f"What is the atomic number of {name}?"] == number


# --- Structure ---------------------------------------------------------------


def test_cards_alternate_symbol_and_number_questions_about_the_same_element() -> None:
    cards = load_flashcards(DECK)

    for index in range(118):
        symbol_name = name_in(SYMBOL_PATTERN, cards[2 * index].front)
        number_name = name_in(NUMBER_PATTERN, cards[2 * index + 1].front)
        assert symbol_name == number_name


def test_atomic_numbers_are_1_to_118_in_order() -> None:
    cards = load_flashcards(DECK)

    numbers = [cards[2 * index + 1].back for index in range(118)]

    assert numbers == [str(number) for number in range(1, 119)]


def test_symbols_are_different_and_well_formed() -> None:
    cards = load_flashcards(DECK)

    symbols = [cards[2 * index].back for index in range(118)]

    assert len(set(symbols)) == 118
    assert all(re.match(r"^[A-Z][a-z]{0,2}$", symbol) for symbol in symbols)


def test_names_are_all_different() -> None:
    cards = load_flashcards(DECK)

    names = [name_in(SYMBOL_PATTERN, cards[2 * index].front) for index in range(118)]

    assert len(set(names)) == 118


def test_all_fronts_are_different() -> None:
    cards = load_flashcards(DECK)

    assert len({card.front for card in cards}) == 236


def test_texts_have_no_outer_spaces_and_are_ascii() -> None:
    # The raw file is read because the loader strips the texts, which would
    # hide a space written in the file.
    raw_cards = json.loads(DECK.read_text(encoding="utf-8"))

    texts = [text for card in raw_cards for text in (card["front"], card["back"])]

    assert all(text == text.strip() for text in texts)
    assert all(text.isascii() for text in texts)


def test_no_front_is_long_enough_to_be_wrapped_in_the_report() -> None:
    cards = load_flashcards(DECK)

    assert max(len(card.front) for card in cards) <= 52


# --- Real games --------------------------------------------------------------

FIRST_FOUR_FRONTS = [
    "Q1: What is the chemical symbol of Hydrogen?",
    "Q2: What is the atomic number of Hydrogen?",
    "Q3: What is the chemical symbol of Helium?",
    "Q4: What is the atomic number of Helium?",
]


def sequential_game_prefix() -> list[str]:
    """Build the lines of the all-correct game of the first four cards."""
    lines: list[str] = []
    for question in FIRST_FOUR_FRONTS:
        lines.extend([question, green("Correct!")])
    return lines + ["Quiz finished.", ""]


def test_sequential_game_with_a_limit_of_four() -> None:
    result = run_ui(["-f", str(DECK), "--limit", "4"], "H", "1", "He", "2")

    assert result.exit_code == 0
    assert result.output[: len(sequential_game_prefix())] == sequential_game_prefix()
    assert parse_report(result.output[len(sequential_game_prefix()) :]) == (
        ParsedReport({"Total questions": "4", "Accuracy": ACC_FULL, "Rank": "S"}, [])
    )


def test_answers_ignore_letter_case() -> None:
    # This is the known limitation of the comparison, which ignores letter
    # case, so "fe" is accepted for "Fe". No pair of symbols of this table
    # differs only by case.
    exact = run_ui(["-f", str(DECK), "--limit", "4"], "H", "1", "He", "2")

    lowered = run_ui(["-f", str(DECK), "--limit", "4"], "h", "1", "HE", "2")

    assert lowered.output == exact.output


def test_random_game_asks_ten_different_cards_of_the_deck() -> None:
    deck_fronts = {card.front for card in load_flashcards(DECK)}

    result = run_ui(["-m", "random", "-f", str(DECK), "--limit", "10"], *["x"] * 10)

    output = result.output
    start = next(i for i, line in enumerate(output) if line.startswith("+="))
    matches = [re.match(r"^Q\d+: (.*)$", line) for line in output]
    asked = [match.group(1) for match in matches if match is not None]
    assert len(asked) == 10
    assert len(set(asked)) == 10
    assert set(asked) <= deck_fronts
    assert output[start - 1] == ""
    assert output[start - 2] == "Quiz finished."
    assert parse_report(output[start:]) == ParsedReport(
        {"Total questions": "10", "Accuracy": ACC_ZERO, "Rank": "D"}, asked
    )


def test_adaptive_game_asks_the_first_five_cards_without_reviews() -> None:
    # The default rest for a deck of 236 cards is 10 questions, so no failed
    # card comes back within 5 questions.
    fronts = [card.front for card in expected_cards()[:5]]

    result = run_ui(["-m", "adaptive", "-f", str(DECK), "--limit", "5"], *["x"] * 5)

    prefix = [
        f"Q1: {fronts[0]}",
        red("Incorrect. Answer: H"),
        f"Q2: {fronts[1]}",
        red("Incorrect. Answer: 1"),
        f"Q3: {fronts[2]}",
        red("Incorrect. Answer: He"),
        f"Q4: {fronts[3]}",
        red("Incorrect. Answer: 2"),
        f"Q5: {fronts[4]}",
        red("Incorrect. Answer: Li"),
        "Quiz finished.",
        "",
    ]
    assert not any("(review)" in line for line in result.output)
    assert result.output[: len(prefix)] == prefix
    assert parse_report(result.output[len(prefix) :]) == ParsedReport(
        {"Total questions": "5", "Accuracy": ACC_ZERO, "Rank": "D"}, fronts
    )


def test_report_with_a_limit_shows_a_finished_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(PROJECT_ROOT)

    result = run_ui(
        ["-f", "data/periodic_table.json", "--limit", "2", "--stats"], "H", "1"
    )

    start = next(i for i, line in enumerate(result.output) if line.startswith("+="))
    assert parse_report(result.output[start:]) == ParsedReport(
        {
            "Mode": "sequential",
            "Deck file": "data/periodic_table.json",
            "Deck size": "236",
            "Session": "finished",
            "Total questions": "2",
            "Correct answers": "2",
            "Incorrect answers": "0",
            "Accuracy": ACC_FULL,
            "Rank": "S",
        },
        [],
    )
