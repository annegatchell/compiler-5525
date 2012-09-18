 #!/usr/bin/python


# parse.py

# Anne Gatchell
# CSCI 5525


# LexToken t:
# t.type which is the token type (as a string)
# t.value which is the lexeme (the actual text matched)
# t.lineno which is the current line number
# t.lexpos which is the position of the token relative to the beginning of the input text

# Context free grammar for P0
#  program ::= module
#             module ::= simple_statement+
#             simple_statement ::= "print" expression
#                                | name "=" expression
#                                | expression
#             expression ::= name
#                          | decimalinteger
#                          | "-" expression
#                          | expression "+" expression
#                          | "(" expression ")"
#                          | "input" "(" ")"

#Reserved word dictionary
# reserved = {
#       'print' : 'PRINT',
#       'input' : 'INPUT',
# }

# # List of token names.   This is always required
# tokens = ['PLUS',
#             'MINUS',
#             'LPAREN',
#             'RPAREN',
#             'EQUALS',
#             'INT',
#             'NAME',] + list(reserved.values())

import sys
import ply.yacc as yacc

#Get token list from the lexer
from lexparse import reserved, tokens
from compiler.ast import *

print_stmts = 0


precedence = (
    ('left', 'PLUS'),
    ('right', 'UMINUS'),
)

def p_module_statment_list(p):
      'module : statement_list'
      p[0] = Module(None, Stmt(p[1]))

def p_statement_list_multi(p):
      'statement_list : statement_list statement'
      p[0] = p[1] + [p[2]]

def p_statement_list_single(p):
      'statement_list : statement'
      p[0] = [p[1]]

def p_print_statement(p):
      'statement : PRINT expression'
      p[0] = Printnl(p[2],None)

def p_name_expression_statement(p):
      'statement : NAME EQUALS expression'
      p[0] = Assign([AssName(p[1],'OP_ASSIGN')], p[3])

def p_statement_expression(p):
      'statement : expression'
      p[0] = Discard(p[1])

def p_int_expression(p):
      'expression : INT'
      p[0] = Const(p[1])

def p_name_expression(p):
      'expression : NAME'
      p[0] = Name(p[1])

def p_statement_unarysub(p):
      'expression : MINUS expression %prec UMINUS'
      p[0] = UnarySub(p[2])

def p_plus_expression(p):
      'expression : expression PLUS expression'
      p[0] = Add((p[1],p[3]))

def p_parens_expression(p):
      'expression : LPAREN expression RPAREN'
      p[0] = p[2]

def p_input(p):
      'expression : INPUT LPAREN RPAREN'
      p[0] = CallFunc(Name('input'),[], None, None)

def p_error(p):
      print "Syntax error at '%s'" % p.value

#Build parser
yacc.yacc()

# Test it out
data = '''
x=4
-input() + 5
print x
'''

#ast = yacc.parse(data)
#print ast

def parse_file(file_path):
      if(print_stmts):
            print 'parse'+file_path
      inputFile = open(file_path)
      source = inputFile.read()
      inputFile.close()

      ast = yacc.parse(source)
      return ast

