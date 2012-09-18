#!/usr/bin/python


# lexparse.py

# Anne Gatchell
# CSCI 5525

"""
Usage: ./lexparse.py <file_name>

"""

import ply.lex as lex

"""
LexToken t:
t.type which is the token type (as a string)
t.value which is the lexeme (the actual text matched)
t.lineno which is the current line number
t.lexpos which is the position of the token relative to the beginning of the input text
"""



#Reserved word dictionary
reserved = {
	'print' : 'PRINT',
	'input' : 'INPUT',
}

# List of token names.   This is always required
tokens = ['PLUS',
		'MINUS',
		'LPAREN',
		'RPAREN',
		'EQUALS',
		'INT',
		'NAME',] + list(reserved.values())

# Regular expression rules for simple tokens
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_INPUT = r'input'
t_EQUALS = r'\='
t_PRINT = r'print'

# A regular expression rule with some action code
def t_INT(t):
    r'\d+'
    try:
    	t.value = int(t.value)
    except ValueError:
    	print "Integer value too large", t.value
    	t.value = 0
    return t

def t_NAME(t):
	r'[a-zA-Z][a-zA-Z_0-9]*'
	t.type = reserved.get(t.value,'NAME')
	return t

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'
# Ignore Comments
t_ignore_COMMENT = r'\#.*'

# Error handling rule
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()




# Test it out
# data = '''
# z = 4
# w = 0
# z1 = 1
# x = w + z1 # x = 1
# y = x + 1  # y = 2
# w1 = y     # w1 = 2
# print w1
# '''

# Give the lexer some input
# lexer.input(data)

# Tokenize
# while True:
#     tok = lexer.token()
#     if not tok: break      # No more input
#     print tok