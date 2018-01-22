import re

from collections import UserString, UserList
from typing import List, Tuple, Dict, Union
from collections import namedtuple
from operator import itemgetter

from samewords.brackets import Brackets

RegistryEntry = Dict[str, Union[List[int], int]]
Registry = List[RegistryEntry]
Element = namedtuple('Element', 'cont pos')


class Macro(UserString):
    """A latex macro, holding information in its name and optional arguments.
    """

    def __init__(self, input_string: str = '') -> None:
        self.data = input_string
        super().__init__(self)
        self.name = self._identify_name()
        self.oarg = self._optional_argument()
        self.empty = self._is_empty()
        self.to_closing = False   # Distance in wordlist to closing bracket.
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
        opening = re.match(r'\\[^ ]+?{', self.data)
        if opening:
            try:
                return self.data[len(opening.group(0))] == '}'
            except IndexError:
                # String ends after opening, so we assume it will have content.
                return False
        # It has no opening, so it has no content.
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
        self.spaces = ''
        self.suffices: List[Element] = []
        self.content: List[Element] = []
        self.punctuation: List[Element] = []
        self.app_list: List[Element] = []
        self.macros: List[Macro] = []
        self.edtext_start = False
        self.edtext_end = False

    def __str__(self) -> str:
        return str(self._get_text())

    def __repr__(self) -> str:
        return "'{}'".format(self._get_text())

    def __eq__(self, other) -> bool:
        return self._get_text() == other

    def __len__(self):
        return len(self.full())

    def _get_text(self):
        return ''.join([c.cont for c in self.content])

    def add_app_entry(self, input_string: str, pos: int, index: int = None):
        """Add apparatus entry to the registry list and return string. If the
        index is provided, add to that index of the list, otherwise append. """
        if index:
            new_cont = self.app_list[index].cont + input_string
            pos = self.app_list[index].pos
            self.app_list[index] = Element(new_cont, pos)
        else:
            self.app_list.append(Element(input_string, pos))

    def full(self) -> str:
        """
        :return: full word including prefix and suffix.
        """
        elements = (
                [(e.cont, e.pos) for e in self.content] +
                [(e.full(), e.pos) for e in self.macros] +
                [(e.cont, e.pos) for e in self.punctuation] +
                [(e.cont, e.pos) for e in self.app_list] +
                [(e.cont, e.pos) for e in self.suffices]
        )

        elements.sort(key=itemgetter(1))
        return ''.join([element[0] for element in elements]) + self.spaces

    def close_macro(self, distance):
        """If there are any open macros on the word, close the last of those.
        This means that we close inner macros first."""
        if self.macros:
            for macro in reversed(self.macros):
                if macro.to_closing is False:
                    macro.to_closing = distance
                    return True
        raise IndexError('The word does not have any open macros.')


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

    def __init__(self, input_str: str = '') -> None:
        """
        self.edtext_brackets: registry of opened brackets at the beginning of
        each edtext macro. Each integer corresponds to a higher level of
        nested edtexts. When a } is hit and the edtext_brackets of that level
        is reached, the encountered } closes the edtext.

        :param input_str: The input string that will be tokenized.
        """
        self.data = input_str
        self._punctuation = re.compile('[!"#$%&\'()*+,-./:;<=>?@\[\]^_`|~–—]+')
        # keep track of current nesting level (zero indexed, so we start at -1)
        self._edtext_lvl = -1
        # keep track of opened brackets at any point
        self._brackets = 0
        # keep track of closing elements in registry process
        self._closures = 0
        # open brackets when starting edtext, to identify apparatus start
        self._stack_edtext = []
        # for indexing into registry after tokenization
        self._stack_registry = []
        # register open bracket count at different positions
        self._stack_bracket = []
        # index available on whole process
        self._index = 0
        # the words list, which needs to be available during any tokenization.
        self._words: Words = Words()
        # the registry list
        self.registry = []
        self.wordlist = self._wordlist()

    def _wordlist(self) -> Words:
        """
        Run the string by tokenizing from each position (subfunction) and
        register the returned Word object if it either opens or closes an
        edtext element.
        """
        pos = 0
        while pos < len(self.data):
            word, pos = self._tokenize(self.data, pos)
            if word.edtext_start:
                count = len([m for m in word.macros if m.name == r'\edtext'])
                while count > 0:
                    self._stack_registry.append(len(self.registry))
                    self.registry.append({'lvl': 0, 'data': [self._index]})
                    count -= 1
            if word.edtext_end:
                while self._closures > 0:
                    reg_index = self._stack_registry.pop()
                    self.registry[reg_index]['data'].append(self._index)
                    self.registry[reg_index]['lvl'] = self._edtext_lvl
                    self._closures -= 1
                    self._edtext_lvl -= 1
            self._words.append(word)
            self._index += 1
        return self._words

    def _tokenize(self, string: str, pos: int = 0) -> Tuple[Word, int]:
        """
        Idea: Run the string and build a Word object. Collect characters,
        digits and hyphens into word.text property. Punctuation goes four
        attributes, `pre_` and `post_` to word and macro. Macros enclosing
        the Word.text are put in the Word.macro property. Opening and closing
        brackets are counted to ensure the timely closing of app notes.
        """
        word = Word()
        while pos < len(string):
            c = string[pos]
            if re.match('[\w\d]', string[pos]):
                match = re.match('[\w\d\-\']+', string[pos:]).group(0)
                word.content.append(Element(match, pos))
                pos += len(match)
                continue
            if re.search(self._punctuation, c):
                # Exception: .5 is part of word, not punctuation.
                if re.match('\.\d', string[pos:]):
                    word.content.append(Element(c, pos))
                    pos += 1
                    continue
                word.punctuation.append(Element(c, pos))
                pos += 1
                continue
            if c == '\\':
                macro = Macro(string[pos:])
                macro.pos = pos
                word.macros.append(macro)
                pos += len(macro)
                if macro.name not in self._content_macros:
                    if macro.opening:
                        pos -= 1    # subtract the opening {
                        bracket_end = pos + len(Brackets(string, pos))
                        macro.hidden_content = string[pos:bracket_end]
                        pos += len(macro.hidden_content)
                    break
                # register position for later closing registration
                self._stack_bracket.append(self._index)
                if macro.name == r'\edtext':
                    self._stack_edtext.append(self._brackets)
                    self._edtext_lvl += 1
                    word.edtext_start = True
                self._brackets += 1
                if macro.empty and not(string[pos].isspace()):
                    # Empty macros cannot have following chars (e.g. A\,B)
                    break
                continue
            if c == '{':
                # Determine of this is an app entry.
                if (self._stack_edtext and
                        self._stack_edtext[-1] == self._brackets):
                    bracket_end = pos + len(Brackets(string, pos))
                    word.add_app_entry(string[pos:bracket_end], pos)
                    word.edtext_end = True
                    pos = bracket_end
                    try:
                        if string[pos] == '}':
                            # Add possible closing of parent first edtext arg
                            word.add_app_entry(string[pos], pos, -1)
                            self._brackets -= 1
                            pos += 1
                    except IndexError:
                        pass
                    self._stack_edtext.pop()
                    self._closures += 1
                    continue
                else:
                    word.suffices.append(Element(c, pos))
                    self._brackets += 1
                    pos += 1
                    continue
            if c == '}':
                # try to register this closing where it opens.
                try:
                    open_idx = self._stack_bracket[-1]
                    self._words[open_idx].close_macro(self._index - open_idx)
                    self._stack_bracket.pop()
                except IndexError:
                    # Word not entered in Words wordlist or it has no macro.
                    # Register on current word macro if it exists.
                    if word.macros:
                        word.close_macro(0)
                        self._stack_bracket.pop()
                self._brackets -= 1
                word.suffices.append(Element(c, pos))
                pos += 1
            if c.isspace():
                word.spaces = re.match('\s+', string[pos:]).group(0)
                pos += len(word.spaces)
                break

        return word, pos
