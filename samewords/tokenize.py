import re

from collections import UserString, UserList
from typing import List, Tuple, Dict, Union

RegistryEntry = Dict[str, Union[List[int], int]]
Registry = List[RegistryEntry]

from samewords.brackets import Brackets

class Macro(UserString):
    """A latex macro, holding information in its name and optional arguments.
    """

    def __init__(self, input_string: str = '') -> None:
        self.data = input_string
        super().__init__(self)
        self.name = self._identify_name()
        self.oarg = self._optional_argument()
        self.empty = self._is_empty()
        self.complete = self._full()

    def __len__(self) -> int:
        return len(self.complete)

    def __repr__(self) -> str:
        return "'{}'".format(self.complete)

    def __str__(self) -> str:
        return str(self.complete)

    def _identify_name(self) -> str:
        """
        A TeX macro can be '\' followed by either a string of letters or
        any single character. Find that.
        """
        if self.data is not '':
            return re.match(r'\\(\w+|.)', self.data).group(0)

    def _optional_argument(self) -> str:
        """
        Identify the possible optinal argument of the marco.
        """
        match = re.match(r'\\[^ ]+(\[[^\]]+\])', self.data)
        if match:
            return match.group(1)
        return ''

    def _is_empty(self) -> bool:
        """
        If the macro contains an opening bracket that is not followed
        immediately by a closing bracket, it has some content.
        """
        opening = re.match(r'\\[^ ]+{', self.data)
        if opening:
            if not(self.data[len(opening.group(0))] == '}'):
                return False
        return True

    def _full(self) -> str:
        opening = re.match(r'[^ ]+?{', self.data)
        if self.data is '':
            return ''
        elif opening:
            return opening.group(0)
        else:
            return self.name


class Word(UserString):

    def __init__(self, chars: str = '') -> None:
        self.data = chars
        super().__init__(self)
        self.text = ''
        self.spaced = False
        self.spaces = ''
        self.prefix = ''
        self.suffix = ''
        self.app_list = []      # List for later use in finding lemmas.
        self.app_string = ''    # String for returning the full word.
        self.macro = Macro()
        self.edtext_start = False
        self.edtext_end = False

    def __str__(self) -> str:
        return str(self.text)

    def __repr__(self) -> str:
        return "'{}'".format(self.text)

    def __eq__(self, other) -> bool:
        return self.text == other

    def __len__(self):
        return len(self.full())

    def add_app_entry(self, input_string, index: int = None):
        """Add apparatus entry to the registry list and return string. If the
        index is provided, add to that index of the list, otherwise append. """
        if index:
            self.app_list[index] += input_string
        else:
            self.app_list.append(input_string)
        self.app_string += input_string

    def full(self) -> str:
        """
        :return: full word including prefix and suffix.
        """
        pref = ''.join(self.prefix)
        suff = ''.join(self.suffix)
        apps = self.app_string
        macro = self.macro.complete
        return pref + macro + self.text + suff + apps + self.spaces


class Words(UserList):

    def __getitem__(self, index):
        cls = type(self)
        if isinstance(index, slice):
            return cls(self.data[index])
        elif isinstance(index, int):
            return self.data[index]
        else:
            msg = '{cls.__name__} indices must be integers'
            raise TypeError(msg.format(cls=cls))

    def write(self) -> str:
        return ''.join([w.full() for w in self.data])

    def clean(self) -> List:
        """A list strings of each Word.text item, i.e. a cleaned word list."""
        return [w.text for w in self.data if w.text]


class Tokenizer:
    in_crit = False
    in_app = False
    edtext_lvl = -1     # zero index the levels
    brackets = 0
    punctuation = re.compile('[!"#$%&\'()*+,-./:;<=>?@\[\]^_`|~–—]+')
    closures = 0


    def __init__(self, input: str = '') -> None:
        """
        self.edtext_brackets: registry of opened brackets at the beginning of
        each edtext macro. Each integer corresponds to a higher level of
        nested edtexts. When a } is hit and the edtext_brackets of that level
        is reached, the encountered } closes the edtext.

        :param input: The input string that will be tokenized.
        """
        self.data = input
        self.registry = []
        self.edtext_brackets = []
        self.open_stack = []
        self.wordlist = self._wordlist()

    def _wordlist(self) -> Words:
        """
        Run the string by tokenizing from each position (subfunction) and
        register the returned Word object if it either opens or closes an
        edtext element.
        """
        words = Words()
        pos = 0
        while pos < len(self.data):
            word, pos = self._tokenize(self.data, pos)
            index = len(words)
            if word.edtext_start:
                self.open_stack.append(len(self.registry))
                self.registry.append({'lvl': self.edtext_lvl, 'data': [index]})
            if word.edtext_end:
                while self.closures > 0:
                    self.registry[self.open_stack[-1]]['data'].append(index)
                    self.open_stack.pop()
                    self.closures -= 1
                    self.edtext_lvl -= 1

            words.append(word)
        return words

    def _tokenize(self, string: str, pos: int = 0) -> Tuple[Word, int]:
        """
        Idea: Run the string and build a Word object. Collect characters,
        digits and hyphens into word.text property. Punctuation goes into
        prefix and suffix properties. Macros enclosing the Word.text are put
        in the Word.macro property. Opening and closing brackets are counted
        to ensure the timely closing of app notes.
        """
        word = Word()
        while pos < len(string):
            c = string[pos]
            if re.match('[\w\d]', string[pos]):
                if '}' in word.suffix:
                    #  Word already has closing brackets, so start a new word
                    break
                match = re.match('[\w\d-]+', string[pos:]).group(0)
                word.text += match
                pos += len(match)
                continue
            if re.search(self.punctuation, c):
                # Exception: .5 is part of word, not punctuation.
                if re.match('\.\d', string[pos:]):
                    word.text += c
                    pos += 1
                    continue
                if word.text:
                    word.suffix += c
                else:
                    word.prefix += c
                pos += 1
                continue
            if c == '\\':
                if word.text:
                    # No appended macros
                    break
                macro = Macro(string[pos:])
                word.macro = macro
                pos += len(macro)
                if macro.empty and not(string[pos].isspace()):
                    # Empty macros cannot have following chars (e.g. A\,B)
                    break
                if macro.name == r'\edtext':
                    self.edtext_brackets.append(self.brackets)
                    self.edtext_lvl += 1
                    word.edtext_start = True
                self.brackets += 1
                continue
            if c == '{':
                # Determine of this is an app entry.
                if (self.edtext_brackets and
                        self.edtext_brackets[-1] == self.brackets):
                    bracket_end = pos + len(Brackets(string, pos))
                    word.add_app_entry(string[pos:bracket_end])
                    pos = bracket_end
                    try:
                        if string[pos] == '}':
                            # Add possible closing of parent first edtext arg
                            word.add_app_entry(string[pos], -1)
                            self.brackets -= 1
                            pos += 1
                    except IndexError:
                        pass
                    word.edtext_end = True
                    self.edtext_brackets.pop()
                    self.closures += 1
                    continue
                else:
                    word.suffix += c
                    pos += 1
                    continue
            if c == '}':
                self.brackets -= 1
                word.suffix += c
                pos += 1
                continue
            if c.isspace():
                word.spaced = True
                word.spaces = re.match('\s+', string[pos:]).group(0)
                pos += len(word.spaces)
                break

        return word, pos
