from samewords.tokenize import Macro


class TestMacro:

    def test_simple_macro(self):
        text = '\emph{content} and something more'
        m = Macro(text)
        assert m.complete == r'\emph{'
        assert m.name == r'\emph'

    def test_optional_argument(self):
        text = '\macro[optional]{content}'
        m = Macro(text)
        assert m.complete == r'\macro[optional]{'
        assert m.name == r'\macro'
        assert m.oarg == r'[optional]'

    def test_unbracketed_macro(self):
        text = '\macro and then some more text'
        m = Macro(text)
        assert m.complete == r'\macro'
        assert m.name == r'\macro'
        assert m.empty == True

    def test_single_char_macro(self):
        text = '\, and then some more text'
        m = Macro(text)
        assert m.complete == r'\,'
        assert m.name == r'\,'
        assert m.empty == True

    def test_empty_bracketed_macro(self):
        text = '\macro{} and more text'
        m = Macro(text)
        assert m.complete == r'\macro{'
        assert m.name == r'\macro'
        assert m.empty == True
