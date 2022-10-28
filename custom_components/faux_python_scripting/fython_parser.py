""" Config Script Parser """
from ctypes.wintypes import WORD
from curses.ascii import isalnum
from multiprocessing.sharedctypes import Value
import re

from collections import namedtuple
from string import punctuation, whitespace
from typing import List, Dict, Literal, NewType

VAR_KW = ["def", "if", "else", "elif", "and", "or", "not", "in", "for"]
WORD_CHAR = "_"
MATH_KW = "+-*/="
QUOTE = "\"'"
PUNCTUATION = "(),:[].}{\"'#"
WHITE_SPACE = "\t "
LINE_BREAK = "\n"

Symbol = namedtuple("Symbol", "word type file_index line_index pos_index")


class SymbolType:
    Punctuation = 0
    Value = 1
    Name = 2
    Whitespace_spacing = 3
    Whitespace_separator = 4
    LineBreak = 5
    MathOperation = 6
    Keyword = 7


class AbstractSyntaxTree:
    pass


class InvalidFythonSyntaxException(ValueError):
    """Exception for invalid syntax"""


def decompose_script(script: str) -> List[str]:
    word_list = []
    word_buffer = []

    char_idx = 0
    while char_idx < len(script):
        char = script[char_idx]
        if char.isalpha() or char.isdigit() or char in WORD_CHAR:
            word_buffer.append(char)

        # Separate symbols based on special characters and line breaks
        elif char in MATH_KW or char in PUNCTUATION or char in LINE_BREAK:
            # Don't add empty strings
            if len(word_buffer) > 0:
                word_list.append("".join(word_buffer))
                word_buffer = []
            word_list += [char]

        # Also Separate symbols based on white space, but needs to be aggregated.
        elif char in WHITE_SPACE:
            # Empty the word buffer if it's needed
            if len(word_buffer) > 0:
                word_list.append("".join(word_buffer))
                word_buffer = []

            # Aggregate all similar white space (spaces with spaces, tabs with tabs)
            word_buffer = [char]
            while char_idx + 1 < len(script) and script[char_idx + 1] == char:
                char_idx += 1
                word_buffer.append(script[char_idx])
            word_list.append("".join(word_buffer))

        else:
            raise InvalidFythonSyntaxException(f"Illegal symbol encountered: {char}")
        char_idx += 1

    # Handle the remaining word in the word buffer
    if len(word_buffer) > 0:
        word_list.append("".join(word_buffer))

    return word_list


def parse_symbols_from_words(word_list: List[str]) -> List[Symbol]:
    symbol_list = []
    line_index = 0
    pos_index = 0
    file_index = 0

    try:
        for word in word_list:
            symbol_type = classify_word(word)
            symbol = Symbol(word, symbol_type, file_index, line_index, pos_index)
            symbol_list.append(symbol)

            # Increment indices
            file_index += len(word)
            if symbol_type == SymbolType.LineBreak:
                pos_index = 0
                line_index += 1
            else:
                pos_index += len(word)

    except InvalidFythonSyntaxException as e:
        raise InvalidFythonSyntaxException(f"Line: {line_index}, Pos: {pos_index}. {e.msg}")


def classify_word(word: str, pos_index) -> SymbolType:
    if len(word) == 1:
        if word in PUNCTUATION:
            return SymbolType.Punctuation
        elif word in MATH_KW:
            return SymbolType.MathOperation
        elif word == "\n":
            return SymbolType.LineBreak

    if word in VAR_KW:
        return SymbolType.Keyword

    if all((w_idx.isalnum() for w_idx in word.split(WORD_CHAR) if len(w_idx) > 0)) and not word[0].isdigit():
        return Symbol.Name

    # All characters are whitespace
    if all((char in WHITE_SPACE for char in word)):
        # What space is used for scope
        if pos_index == 0:
            return SymbolType.Whitespace_spacing
        else:
            return SymbolType.Whitespace_separator

    try:
        float(word)
        return Symbol.Value
    except ValueError:
        # We've run out of tests.  `word` could not be classified.
        raise InvalidFythonSyntaxException(f"invalid Syntax: Unidentified symbol detected {word}")


def parse_ast_from_symbols(symbol_list: List[Symbol]) -> AbstractSyntaxTree:
    ast = AbstractSyntaxTree()
    word_index = 0
    [next_node, word_index] = _parse_node(word_list, word_index, timezone)
    program.append(next_node)
    while word_index < len(word_list):
        [next_node, word_index] = _parse_node(word_list, word_index, timezone)
        program.append(next_node)
    return program


class SyntaxNode:
    pass

class LiteralNode(SyntaxNode):
    pass


def extract_quote(symbol_index, symbol_list, initiating_symbol):
    quote_value_list = []
    symbol = symbol_list[symbol_index]
    while symbol.value != initiating_symbol.value:
        quote_value_list.append(symbol.value)
        symbol_index += 1
        symbol = symbol_list[symbol_index]
    return ("".join(quote_value_list), symbol_index + 1)


def parse_symbol_to_syntax_node(symbol_index: int, symbol_list: List[Symbol]) -> SyntaxNode:
    symbol = symbol_list[symbol_index]
    if symbol.type in SymbolType.Punctuation:
        if symbol.value in QUOTE:
            quote_value, symbol_index = extract_quote(symbol_index + 1, symbol_list, initiating_symbol=symbol))
            return LiteralNode(quote_value, symbol), symbol_index
        if symbol.value in ATTRIBUTE_ACCESSOR:
            get_attribute(symbol_index + 1, symbol_list)
    if symbol.type in SymbolType.Name:
        node = SyntaxNode()
        word_index += 1
    elif word in MATH_KW:
        node = {"type": "arithmatic", "value": word}
        word_index += 1
    elif re.search(CLOCK_REGEX, word):
        node = {"type": "var", "value": _parse_24h_clock(word)}
        word_index += 1
    elif re.search(FLOAT_REGEX, word):
        node = {"type": "var", "value": float("".join(word.split("_")))}
        word_index += 1
    elif re.search(DURATION_REGEX, word):
        node = {"type": "var", "value": _parse_duration(word)}
        word_index += 1
    elif word in VAR_KW:
        node = {"type": "var", "value": time.normalize_time(word)}
        word_index += 1
    else:
        # ANY UNKOWN WORDS ARE TREATED AS STRING LITERALS
        node = {"type": "var", "value": word}
    return [node, word_index]


def _parse_node(word_list, word_index, timezone):
    word = word_list[word_index]
    if word in FUNCTION_KW:
        node = {"type": "func", "value": word}
        [node["args"], word_index] = _parse_args(word_list, word_index + 1, timezone)
    elif word in PUNCTUATION:
        node = {"type": "punc", "value": word}
        word_index += 1
    elif word in MATH_KW:
        node = {"type": "arithmatic", "value": word}
        word_index += 1
    elif re.search(CLOCK_REGEX, word):
        node = {"type": "var", "value": _parse_24h_clock(word)}
        word_index += 1
    elif re.search(FLOAT_REGEX, word):
        node = {"type": "var", "value": float("".join(word.split("_")))}
        word_index += 1
    elif re.search(DURATION_REGEX, word):
        node = {"type": "var", "value": _parse_duration(word)}
        word_index += 1
    elif word in VAR_KW:
        node = {"type": "var", "value": time.normalize_time(word)}
        word_index += 1
    else:
        # ANY UNKOWN WORDS ARE TREATED AS STRING LITERALS
        node = {"type": "var", "value": word}
    return [node, word_index]


def _parse_args(word_list, word_index, timezone):
    [next_node, word_index] = _parse_node(word_list, word_index, timezone)
    if next_node["type"] != "punc" or next_node["value"] != "(":
        raise InvalidSyntaxException(f"Expected ( at word: {word_index}")

    args = []
    prog = []
    while next_node["type"] != "punc" or next_node["value"] != ")":
        [next_node, word_index] = _parse_node(word_list, word_index, timezone)
        if next_node["type"] == "punc" and next_node["value"] == ",":
            args.append(prog)
            prog = []
        elif next_node["type"] == "punc" and next_node["value"] == ")":
            pass
        else:
            prog.append(next_node)
    args.append(prog)
    return [args, word_index]
