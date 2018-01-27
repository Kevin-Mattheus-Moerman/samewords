# This is the settings files. The variables hare are generally modified at runtime (as command line
# arguments), but can also be modified manually in here.

exclude_macros = [
    '\\Afootnote',
    '\\Bfootnote',
    '\\Cfootnote',
    '\\Dfootnote',
    '\\Efootnote',
    '\\lemma',
    '\\applabel',
]

# Macros that should be included when identifying matches
include_macros = [
    '\\index',  # because Sortes\index[persons]{Socrates} ≠ Sortes\index[persons]{Sortes}
]

# List of patterns that should be included when matching for ellipsis symbols in `\lemma{}`. These
# are used in a regular expression match, so any valid python regular expression will work.
ellipsis_patterns = [
    r'\\l?dots({})?',   # \dots, \dots{}, \ldots, \ldots{}
    '-+',               # one or more dashes
    '–',                # one or more en-dash
    '—'                 # em-dash
]
