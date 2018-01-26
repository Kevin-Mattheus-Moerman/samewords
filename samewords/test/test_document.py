from samewords.document import *


def test_document_content():
    with open('./samewords/test/assets/da-49-l1q1.tex', 'rb') as f:
        content = f.read().decode('utf-8')
    assert document_content('./samewords/test/assets/da-49-l1q1.tex') == content


class TestParagraphHandling:
    document = document_content('./samewords/test/assets/simple.tex')

    before = r"""\documentclass[a4paper, 12pt]{book}

% latin language
\usepackage{polyglossia}
\setmainlanguage{english}
\setotherlanguage{latin}

% reledmac settings
\usepackage[final]{reledmac}


% custom macros
\newcommand{\name}[1]{#1}
\newcommand{\lemmaQuote}[1]{\textsc{#1}}
\newcommand{\worktitle}[1]{\textit{#1}}
\newcommand{\supplied}[1]{⟨#1⟩}
\newcommand{\suppliedInVacuo}[1]{$\ulcorner$#1$\urcorner$}
\newcommand{\secluded}[1]{{[}#1{]}}
\newcommand{\metatext}[1]{<#1>}
\newcommand{\hand}[1]{\textsuperscript{#1}}
\newcommand{\del}[1]{[#1 del. ms]}
\newcommand{\no}[1]{\emph{#1}\quad}
\newcommand{\corruption}[1]{\textdagger#1\textdagger}

\begin{document}

\begin{latin}
\beginnumbering
"""
    inside = r"""
\pstart[\subsection*{\metatext{De scientia}}]
\edlabelS{da-49-l1q1-274hkz}%
\ledsidenote{B 148va}\ledsidenote{O 164rb}%
\edtext{Item}{\lemma{Item}\Bfootnote{\emph{om.} B}}
quaeratur\edtext{}{\lemma{}\Bfootnote[nosep]{nunc \emph{post} quaeratur B}}
primo utrum de anima possit nobis acquiri scientia.
\edlabelE{da-49-l1q1-274hkz}
\pend

\medbreak

\pstart[\medbreak{}]
\edlabelS{da-49-l1q1-j01jdw}%
\no{1}
Videtur quod non.
\edlabelE{da-49-l1q1-j01jdw}
\pend

\pstart
\edlabelS{da-49-l1q1-ysmgk1}%
\no{1.1}
Illud de quo est scientia est intelligibile, quia cum scientia sit habitus
intellectus, de quo est scientia oportet esse intelligibile; sed anima non est
intelligibile, quia omnis nostra cognitio ortum habet a sensu, \edtext{unde
  ipsum intelligere non est}{\lemma{unde \dots{} est}\Bfootnote{quia nihil
    intelligimus B}} sine phantasmate, sed anima sub sensu non cadit, nec
phantasma facit; ergo et cetera.
\edlabelE{da-49-l1q1-ysmgk1}
\pend

\pstart
\edlabelS{da-49-l1q1-mjzkyp}%
\no{1.2}
Praeterea, unum et idem non potest esse simul movens et motum,
quia\edtext{}{\lemma{}\Bfootnote[nosep]{si \emph{post} quia B}} sic \edtext{idem
  esset}{\lemma{idem esset}\Bfootnote{\emph{inv.} B}} actu et potentia respectu
eiusdem; sed cognitum est movens respectu cognocentis; ergo unum et idem non
potest esse \edtext{cognoscens}{\lemma{cognoscens}\Bfootnote{movens B}} et
\edtext{cognitum}{\lemma{cognitum}\Bfootnote{motum
    B}},\edtext{}{\lemma{}\Bfootnote[nosep]{sed \emph{post} motum B}} hoc tamen
contingeret si de anima \edtext{esset scientia}{\lemma{esset
    scientia}\Bfootnote{cognitionem haberemus B}}.
\edlabelE{da-49-l1q1-mjzkyp}
\pend
"""
    after = r"""
\endnumbering
\end{latin}
\end{document}
"""

    def test_chunk_paragraphs(self):
        chunking = chunk_document(self.document)
        assert chunking['before'] == self.before
        assert chunking['inside'] == self.inside
        assert chunking['after'] == self.after






