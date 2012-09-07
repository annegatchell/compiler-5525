#!/usr/bin/python


#compile.py

# Anne Gatchell
# CSCI 5525

"""
Usage: compile.py <file_name>

"""
import sys
import compiler
from compiler.ast import *

temp_counter = -1

def temp_gen(basename):
	global temp_counter
	temp_counter += 1
	return basename + str(temp_counter)



def flatten(ast):
	if isinstance(ast,Module):
		#print ast
		return Module(ast.doc, flatten(ast.node))
	if isinstance(ast,Stmt):
		fnodes = map(flatten, ast.nodes)
		fnodes = sum(fnodes, [])
		print 'fnodes\n',fnodes
		return Stmt(fnodes)
	if isinstance(ast, Printnl):
		fnodes = map(flatten, ast.nodes)
		print fnodes
		print_ = sum(fnodes, [])
		return Printnl(print_, ast.dest)

	#if isinstance(ast, Name):
		#print ast
	#	return(ast,[])
	#if isinstance(ast, Add):
		#print ast



def main():
	platform = sys.platform
	print 'Running on a',platform
	if(len(sys.argv) != 2):
		print 'Usage: compile.py <file_name>'
		return 1;
	print 'hello there,', sys.argv[1]
	inputFile = sys.argv[1]
	ast = compiler.parseFile(inputFile);

	print ast, '\n\n\n'
	fast = flatten(ast)
	print 'flatten(ast)\n',fast


if __name__ == '__main__':
	main();