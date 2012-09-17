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
from x86ast import *



temp_counter = -1

def temp_gen(basename):
	global temp_counter
	temp_counter += 1
	return basename + str(temp_counter)

def is_leaf(ast):
    return isinstance(ast, Const) or isinstance(ast, Name)

def flatten(ast):
	if isinstance(ast,Module):
		print 'IN MODULE', Module(ast.doc, flatten(ast.node))
		return Module(ast.doc, flatten(ast.node))
	elif isinstance(ast,Stmt):
		#print 'STMT'
		fnodes = []
		fnodes = map(flatten, ast.nodes)
		#print 'fnodes before sum', fnodes
		fnodes = sum(fnodes, [])
		#print 'fnodes after sum',fnodes
		print 'IN STMT',Stmt(fnodes)
		return Stmt(fnodes)
	elif isinstance(ast, Printnl):
		nodes = map(flatten, ast.nodes)
		prints = []
		for (t,l) in nodes:
			if not is_leaf(t):
				temp = temp_gen('print')
				l.append(Assign([AssName(temp, 'OP_ASSIGN')], t))
				prints.append(Name(temp))
			else:
				prints.append(t)
		stmts = sum([l for (t, l) in nodes], [])
		print 'IN PRINT STATEMENTS',stmts + [Printnl(prints, ast.dest)]
		return stmts + [Printnl(prints, ast.dest)]
	elif isinstance(ast, Assign):
		#print 'ASSIGN'
		#print 'assign',ast
		fnodes = map(flatten, ast.nodes)
		assigns = [t for (t, l) in fnodes]
		stmts = sum([l for (t, l) in fnodes], [])
		targ_node, targ_stmts = flatten(ast.expr)
		print 'IN ASSIGN',(stmts + targ_stmts + [Assign(assigns, targ_node)])
		return stmts + targ_stmts + [Assign(assigns, targ_node)]
	elif isinstance(ast, AssName):
		#print 'ASSNAME'
		print 'IN ASS NAME',(ast, [])
		return (ast,[])
	elif isinstance(ast, Discard):
		#print 'DISCARD'
		expr, stmts = flatten(ast.expr)
		print 'IN DISCARD', stmts + [Discard(expr)]
		return stmts + [Discard(expr)]
	elif isinstance(ast, Const):
		print 'IN THE CONST', (ast,[])
		return (ast,[])
	elif isinstance(ast, Name):
		print 'IN THE NAME', (ast, [])
		return (ast, [])
	elif isinstance(ast, Add):
		#print 'ADD'
		lexpr, lstmts = flatten(ast.left)
		rexpr, rstmts = flatten(ast.right)
		if not is_leaf(lexpr):
			temp = temp_gen("left")
			lstmts.append(Assign([AssName(temp, 'OP_ASSIGN')], lexpr))
			lexpr = Name(temp)
		if not is_leaf(rexpr):
			temp = temp_gen("right")
			rstmts.append(Assign([AssName(temp, 'OP_ASSIGN')], rexpr))
			rexpr = Name(temp)
		print 'IN THE ADD',(Add((lexpr, rexpr)), lstmts + rstmts)
		return (Add((lexpr, rexpr)), lstmts + rstmts)
	elif isinstance(ast, UnarySub):
		#print 'UNARYSUB'
		expr, stmts = flatten(ast.expr)
		if not is_leaf(expr):
			temp = temp_gen("usub")
			stmts.append(Assign([AssName(temp, 'OP_ASSIGN')], expr))
			expr = Name(temp)
		print 'IN THE UNARYSUB',(UnarySub(expr), stmts)
		return (UnarySub(expr), stmts)
	elif isinstance(ast, CallFunc):
		#print 'CALLFUNC'
		expr, stmts = flatten(ast.node)
		if not is_leaf(expr):
			temp = temp_gen("func")
			stmts.append(Assign([AssName(temp, 'OP_ASSIGN')], expr))
			expr = Name(temp)
		args_exprs = []
		args_stmts = []
		for arg in ast.args:
			arg_expr, arg_stmts = flatten(arg)
			if not is_leaf(arg_expr):
				temp = temp_gen("arg")
				arg_stmts.append(Assign([AssName(temp, 'OP_ASSIGN')], arg_expr))
				arg_expr = Name(temp)
			args_exprs.append(arg_expr)
			args_stmts = args_stmts + arg_stmts
		print 'IN THE CALLFUNC', (CallFunc(expr, args_exprs), stmts + args_stmts)
		return (CallFunc(expr, args_exprs), stmts + args_stmts)
	else:
	 	raise Exception('Error in flatten: unrecognized AST node')

def scan_allocs(ast):
	if isinstance(ast, Module):
		return scan_allocs(ast.node)
	elif isinstance(ast, Stmt):
		return reduce(lambda x,y: x.union(y), map(scan_allocs, ast.nodes), set([]))
	elif isinstance(ast, Assign):
		return reduce(lambda x,y: x.union(y), map(scan_allocs, ast.nodes), set([]))
	elif isinstance(ast, AssName):
		return set([ast.name])
	else:
		return set([])

current_offset = 0
stack_map = {}
def allocate(var, size):
	global current_offset, stack_map
	if var in stack_map:
		return stack_map[var]
	current_offset = size + current_offset
	stack_map[var] = current_offset
	return current_offset

# Mike's Instruction Select
EAX = Reg86('eax')
EBP = Reg86('ebp')
ESP = Reg86('esp')
def instr_select(ast, value_mode=Move86):
	global stack_map
	if isinstance(ast, Module):
		return [Push86(EBP), Move86(ESP, EBP), Sub86(Const86(len(scan_allocs(ast)) * 4), ESP)] + instr_select(ast.node) + [Move86(Const86(0), EAX), Leave86(), Ret86()]
	elif isinstance(ast, Stmt):
		return sum(map(instr_select, ast.nodes),[])
	elif isinstance(ast, Printnl):
		return instr_select(ast.nodes[0]) + [Push86(EAX), Call86('print_int_nl'), Add86(Const86(4), ESP)]
	elif isinstance(ast, Assign):
		expr_assemb = instr_select(ast.expr)
		offset = allocate(ast.nodes[0].name, 4)
		return expr_assemb + [Move86(EAX, Mem86(offset, EBP))]
	elif isinstance(ast, Discard):
		return instr_select(ast.expr)
	elif isinstance(ast, Add):
		return instr_select(ast.left) + instr_select(ast.right, value_mode=Add86)
	elif isinstance(ast, UnarySub):
		return instr_select(ast.expr) + [Neg86(EAX)]
	elif isinstance(ast, CallFunc):
		return [Call86('input')]
	elif isinstance(ast, Const):
		return [value_mode(Const86(ast.value), EAX)]
	elif isinstance(ast, Name):
		return [value_mode(Mem86(stack_map[ast.name], EBP), EAX)]
	else:
		raise Exception("Unexpected term: " + str(ast))

word_size = 4
def compile_stmt(ast, value_mode='movl'):
	global stack_map
	if isinstance(ast, Module):
		header = ['pushl %ebp',
				'movl %esp, %ebp',
				('subl $%d, %%esp' % (len(scan_allocs(ast)) * word_size))]
		footer = ['movl $0, %eax', 'leave', 'ret']
		return header + compile_stmt(ast.node) + footer
	elif isinstance(ast, Stmt):
		return sum(map(compile_stmt, ast.nodes),[])
	elif isinstance(ast, Printnl):
		return compile_stmt(ast.nodes[0]) + ['pushl %eax',
												'call print_int_nl',
												('addl $%d, %%esp' % word_size)]
	elif isinstance(ast, Assign):
		expr_assemb = compile_stmt(ast.expr)
		offset = allocate(ast.nodes[0].name, word_size)
		return expr_assemb + [('movl %%eax, -%d(%%ebp)' % offset)]
	elif isinstance(ast, Discard):
		return compile_stmt(ast.expr)
	elif isinstance(ast, Add):
		return compile_stmt(ast.left) + compile_stmt(ast.right, value_mode='addl')
	elif isinstance(ast, UnarySub):
		return ['negl %eax']
	elif isinstance(ast, CallFunc):
		return ['call input']
	elif isinstance(ast, Const):
		return [('%s $%d, %%eax' % (value_mode, ast.value))]
	elif isinstance(ast, Name):
		return [('%s -%d(%%ebp), %%eax' % (value_mode, stack_map[ast.name]))]
	else:
		raise Exception("Unexpected term: " + str(ast))

def write_to_file(assembly, outputFileName):
	"""Function to write assembly to file"""
	assembly = '.globl main\nmain:\n\t' + '\n\t'.join(assembly)
	outputfile = open(outputFileName, 'w+')
	outputfile.write(assembly + '\n')
	outputfile.close()


def main():
	platform = sys.platform
	#print 'Running on a',platform
	if(len(sys.argv) != 2):
		sys.stderr.write(str(argv[0]) + " requires two arguments\n")
		return 1;
	inputFile = sys.argv[1]
	inputFilePath = str(sys.argv[1])
	if(inputFilePath[-3:] != ".py"):
		sys.stderr.write(str(argv[0]) + " input file must be of type *.py\n")
		return 1
	outputFilePath = inputFilePath.split('/')
	outputFileName = (outputFilePath[-1:])[0]
	outputFileName = outputFileName[:-3] + ".s"

	print inputFile
	ast = compiler.parseFile(inputFile);

	print ast, '\n\n\n'
	fast = flatten(ast)

	#print 'flatten(ast)\n',fast
	print fast
	assembly = instr_select(fast)
	print assembly

	write_to_file(map(str, assembly), outputFileName)

	return 0

if __name__ == '__main__':
	main();

