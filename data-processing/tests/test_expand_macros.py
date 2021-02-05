from typing import List

from common.expand_macros import Expansion, detect_expansions


def to_bytes(*lines: List[str]) -> bytes:
    return "\n".join(lines).encode()


def test_detect_simple_macro():
    # In each of these test cases, the log in the variable 'log' was generated by running our
    # instrumented version of LaTeXML (https://github.com/allenai/LaTeXML) on a TeX document.
    # The relevant excerpt of the input document is shown for each test case as "Input TeX".

    # Input TeX:
    # \def\simpledef{x}
    # $\simpledef$
    log = to_bytes(
        r"Start of expansion. Control sequence: T_CS[\simpledef]. (object ID: 1). Current expansion depth: 1. (If this was a literal control sequence in a file rather than from an expansion, it appeared in /path/to/main.tex from line 2, col 1 to line 2, col 11).",
        r"Expansion token: x (object ID 2). Category: 11. Expandable: false.",
        r"End of expansion (object ID: 1). Current expansion depth: 1. Expansion: x.",
    )
    expansions = list(detect_expansions(log, in_files=["/path/to/main.tex"]))
    assert len(expansions) == 1
    assert expansions[0] == Expansion(rb"\simpledef", 2, 1, 2, 11, b"x")


def test_detect_multiple_macros():
    # Input TeX:
    # \def\simpledef{x}
    # $\simpledef$
    # $\simpledef$
    log = to_bytes(
        r"Start of expansion. Control sequence: T_CS[\simpledef]. (object ID: 1). Current expansion depth: 1. (If this was a literal control sequence in a file rather than from an expansion, it appeared in /path/to/main.tex from line 2, col 1 to line 2, col 11).",
        r"Expansion token: x (object ID 2). Category: 11. Expandable: false.",
        r"End of expansion (object ID: 1). Current expansion depth: 1. Expansion: x.",
        r"Start of expansion. Control sequence: T_CS[\simpledef]. (object ID: 3). Current expansion depth: 1. (If this was a literal control sequence in a file rather than from an expansion, it appeared in /path/to/main.tex from line 3, col 1 to line 3, col 11).",
        r"Expansion token: x (object ID 4). Category: 11. Expandable: false.",
        r"End of expansion (object ID: 3). Current expansion depth: 1. Expansion: x.",
    )
    expansions = list(detect_expansions(log, in_files=["/path/to/main.tex"]))
    assert len(expansions) == 2
    assert expansions[0] == Expansion(rb"\simpledef", 2, 1, 2, 11, b"x")
    assert expansions[1] == Expansion(rb"\simpledef", 3, 1, 3, 11, b"x")


def test_detect_macro_containing_style_macro():
    # Input TeX:
    # \def\defcontainingstylecontrolsequence{\mathbf x}
    # $\defcontainingstylecontrolsequence$2
    log = to_bytes(
        r"Start of expansion. Control sequence: T_CS[\defcontainingstylecontrolsequence]. (object ID: 1). Current expansion depth: 1. (If this was a literal control sequence in a file rather than from an expansion, it appeared in /path/to/main.tex from line 2, col 1 to line 2, col 35).",
        r"Expansion token: \mathbf (object ID 2). Category: 16. Expandable: false.",
        r"Expansion token: x (object ID 3). Category: 11. Expandable: false.",
        r"End of expansion (object ID: 1). Current expansion depth: 1. Expansion: \mathbfx.",
    )
    expansions = list(detect_expansions(log, in_files=["/path/to/main.tex"]))
    assert len(expansions) == 1
    assert expansions[0] == Expansion(
        rb"\defcontainingstylecontrolsequence", 2, 1, 2, 35, rb"\mathbf x"
    )


def test_detect_macro_with_arguments():
    # Input TeX:
    # \def\defwithargs#1#2{#1 + #2}
    # $\defwithargs{x}{y}$
    log = to_bytes(
        r"Start of expansion. Control sequence: T_CS[\defwithargs]. (object ID: 1). Current expansion depth: 1. (If this was a literal control sequence in a file rather than from an expansion, it appeared in /path/to/main.tex from line 2, col 1 to line 2, col 13).",
        r'Argument token: "{" (source file /path/to/main.tex, from line 2 col 13 to line 2 col 14).',
        r'Argument token: "x" (source file /path/to/main.tex, from line 2 col 14 to line 2 col 15).',
        r'Argument token: "}" (source file /path/to/main.tex, from line 2 col 15 to line 2 col 16).',
        r'Argument token: "{" (source file /path/to/main.tex, from line 2 col 16 to line 2 col 17).',
        r'Argument token: "y" (source file /path/to/main.tex, from line 2 col 17 to line 2 col 18).',
        r'Argument token: "}" (source file /path/to/main.tex, from line 2 col 18 to line 2 col 19).',
        r"Expansion token: x (object ID 2). Category: 11. Expandable: false.",
        r"Expansion token:   (object ID 3). Category: 10. Expandable: false.",
        r"Expansion token: + (object ID 4). Category: 12. Expandable: false.",
        r"Expansion token:   (object ID 3). Category: 10. Expandable: false.",
        r"Expansion token: y (object ID 5). Category: 11. Expandable: false.",
        r"End of expansion (object ID: 1). Current expansion depth: 1. Expansion: x + y.",
    )
    expansions = list(detect_expansions(log, in_files=["/path/to/main.tex"]))
    assert len(expansions) == 1
    assert expansions[0] == Expansion(rb"\defwithargs", 2, 1, 2, 19, b"x + y")


def test_detect_macro_with_macro_in_expansion():
    # \def\simpledef{x}
    # \def\defcontainingcontrolsequence{\simpledef + y}
    # $\defcontainingcontrolsequence$
    log = to_bytes(
        r"Start of expansion. Control sequence: T_CS[\defcontainingcontrolsequence]. (object ID: 1). Current expansion depth: 1. (If this was a literal control sequence in a file rather than from an expansion, it appeared in /path/to/main.tex from line 2, col 1 to line 2, col 30).",
        r"Expansion token: \simpledef (object ID 2). Category: 16. Expandable: true.",
        r"Expansion token: + (object ID 3). Category: 12. Expandable: false.",
        r"Expansion token:   (object ID 4). Category: 10. Expandable: false.",
        r"Expansion token: y (object ID 5). Category: 11. Expandable: false.",
        r"End of expansion (object ID: 1). Current expansion depth: 1. Expansion: \simpledef+ y.",
        r"Start of expansion. Control sequence: T_CS[\simpledef]. (object ID: 2). Current expansion depth: 1. (If this was a literal control sequence in a file rather than from an expansion, it appeared in /path/to/main.tex from line 2, col 1 to line 2, col 30).",
        r"Expansion token: x (object ID 6). Category: 11. Expandable: false.",
        r"End of expansion (object ID: 2). Current expansion depth: 1. Expansion: x.",
    )
    expansions = list(detect_expansions(log, in_files=["/path/to/main.tex"]))
    assert len(expansions) == 1
    assert expansions[0] == Expansion(
        rb"\defcontainingcontrolsequence", 2, 1, 2, 30, b"x+ y"
    )


def test_detect_macro_with_macro_in_argument():
    # Input TeX:
    # \def\simpledef{x}
    # \def\defwithargs#1#2{#1 + #2}
    # $\defwithargs{\simpledef}{y}$
    log = to_bytes(
        r"Start of expansion. Control sequence: T_CS[\defwithargs]. (object ID: 1). Current expansion depth: 1. (If this was a literal control sequence in a file rather than from an expansion, it appeared in /path/to/main.tex from line 2, col 1 to line 2, col 13).",
        r'Argument token: "{" (source file /path/to/main.tex, from line 2 col 13 to line 2 col 14).',
        r'Argument token: "\simpledef" (source file /path/to/main.tex, from line 2 col 14 to line 2 col 24).',
        r'Argument token: "}" (source file /path/to/main.tex, from line 2 col 24 to line 2 col 25).',
        r'Argument token: "{" (source file /path/to/main.tex, from line 2 col 25 to line 2 col 26).',
        r'Argument token: "y" (source file /path/to/main.tex, from line 2 col 26 to line 2 col 27).',
        r'Argument token: "}" (source file /path/to/main.tex, from line 2 col 27 to line 2 col 28).',
        r"Expansion token: \simpledef (object ID 2). Category: 16. Expandable: true.",
        r"Expansion token:   (object ID 3). Category: 10. Expandable: false.",
        r"Expansion token: + (object ID 4). Category: 12. Expandable: false.",
        r"Expansion token:   (object ID 3). Category: 10. Expandable: false.",
        r"Expansion token: y (object ID 5). Category: 11. Expandable: false.",
        r"End of expansion (object ID: 1). Current expansion depth: 1. Expansion: \simpledef + y.",
        r"Start of expansion. Control sequence: T_CS[\simpledef]. (object ID: 2). Current expansion depth: 1. (If this was a literal control sequence in a file rather than from an expansion, it appeared in /path/to/main.tex from line 2, col 27 to line 2, col 28).",
        r"Expansion token: x (object ID 6). Category: 11. Expandable: false.",
        r"End of expansion (object ID: 2). Current expansion depth: 1. Expansion: x.",
    )
    expansions = list(detect_expansions(log, in_files=["/path/to/main.tex"]))
    assert len(expansions) == 1
    assert expansions[0] == Expansion(rb"\defwithargs", 2, 1, 2, 28, b"x + y")


def test_detect_macro_ignore_operator_wrapper():
    # Input TeX:
    # \usepackag{amsmath}
    # \DeclareMathOperator{\op}{op}
    # $\op x$
    log = to_bytes(
        r"Start of expansion. Control sequence: T_CS[\op]. (object ID: 1). Current expansion depth: 1. (If this was a literal control sequence in a file rather than from an expansion, it appeared in /path/to/main.tex from line 2, col 1 to line 2, col 4).",
        r"Expansion token: \op@wrapper (object ID 2). Category: 16. Expandable: false.",
        r"Expansion token: { (object ID 3). Category: 1. Expandable: false.",
        r"Expansion token: \op@presentation (object ID 4). Category: 16. Expandable: true.",
        r"Expansion token: } (object ID 5). Category: 2. Expandable: false.",
        r"End of expansion (object ID: 1). Current expansion depth: 1. Expansion: \op@wrapper{\op@presentation}.",
        r"Start of expansion. Control sequence: T_CS[\op@presentation]. (object ID: 4). Current expansion depth: 1. (If this was a literal control sequence in a file rather than from an expansion, it appeared in  from line 0, col 0 to line 0, col 0).",
        r"Expansion token: \operatorname (object ID 6). Category: 16. Expandable: false.",
        r"Expansion token: { (object ID 3). Category: 1. Expandable: false.",
        r"Expansion token: o (object ID 7). Category: 11. Expandable: false.",
        r"Expansion token: p (object ID 8). Category: 11. Expandable: false.",
        r"Expansion token: } (object ID 5). Category: 12. Expandable: false.",
        r"End of expansion (object ID: 4). Current expansion depth: 1. Expansion: \operatorname{op}.        ",
    )
    expansions = list(detect_expansions(log, in_files=["/path/to/main.tex"]))
    assert len(expansions) == 1
    assert expansions[0] == Expansion(rb"\op", 2, 1, 2, 4, rb"{\operatorname{op}}")


# def test_fail_me_2():
#     assert (
#         False
#     ), "Will probably break if a token expands to another macro with arguments, as those arguments will need to be removed. May be able to add some additional logic in the argument reader routine switch case."
