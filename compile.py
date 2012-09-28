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
from semix86 import *
from parse import parse_file


print_stmts = 0

temp_counter = -1



def temp_gen(basename):
	global temp_counter
	temp_counter += 1
	return basename + str(temp_counter)

def is_leaf(ast):
    return isinstance(ast, Const) or isinstance(ast, Name)

def flatten(ast):
	if isinstance(ast,Module):
		if(print_stmts):
			print 'IN MODULE', Module(ast.doc, flatten(ast.node))
		return Module(ast.doc, flatten(ast.node))
	elif isinstance(ast,Stmt):
		#print 'STMT'
		fnodes = []
		fnodes = map(flatten, ast.nodes)
		#print 'fnodes before sum', fnodes
		fnodes = sum(fnodes, [])
		#print 'fnodes after sum',fnodes
		if(print_stmts):
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
		if(print_stmts):
			print 'IN PRINT STATEMENTS',stmts + [Printnl(prints, ast.dest)]
		return stmts + [Printnl(prints, ast.dest)]
	elif isinstance(ast, Assign):
		#print 'ASSIGN'
		#print 'assign',ast
		fnodes = map(flatten, ast.nodes)
		assigns = [t for (t, l) in fnodes]
		stmts = sum([l for (t, l) in fnodes], [])
		targ_node, targ_stmts = flatten(ast.expr)
		if(print_stmts):
			print 'IN ASSIGN',(stmts + targ_stmts + [Assign(assigns, targ_node)])
		return stmts + targ_stmts + [Assign(assigns, targ_node)]
	elif isinstance(ast, AssName):
		#print 'ASSNAME'
		if(print_stmts):
			print 'IN ASS NAME',(ast, [])
		return (ast,[])
	elif isinstance(ast, Discard):
		#print 'DISCARD'
		expr, stmts = flatten(ast.expr)
		temp = temp_gen("discard")
		stmts.append(Assign([AssName(temp, 'OP_ASSIGN')], expr))
		#expr = Name(temp)
		if(print_stmts):
			print 'IN DISCARD', stmts + [Discard(expr)]
		return stmts
	elif isinstance(ast, Const):
		if(print_stmts):
			print 'IN THE CONST', (ast,[])
		return (ast,[])
	elif isinstance(ast, Name):
		if(print_stmts):
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
		if(print_stmts):
			print 'IN THE ADD',(Add((lexpr, rexpr)), lstmts + rstmts)
		return (Add((lexpr, rexpr)), lstmts + rstmts)
	elif isinstance(ast, UnarySub):
		#print 'UNARYSUB'
		expr, stmts = flatten(ast.expr)
		if not is_leaf(expr):
			temp = temp_gen("usub")
			stmts.append(Assign([AssName(temp, 'OP_ASSIGN')], expr))
			expr = Name(temp)
		if(print_stmts):
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
		if(print_stmts):
			print 'IN THE CALLFUNC', (CallFunc(expr, args_exprs), stmts + args_stmts)
		return (CallFunc(expr, args_exprs), stmts + args_stmts)
	else:
	 	raise Exception('Error in flatten: unrecognized AST node'+ str(ast))

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


EAX = Reg86('eax')
EBP = Reg86('ebp')
ESP = Reg86('esp')

def instr_select_vars(ast, value_mode=Move86):
	if isinstance(ast,Module):
		return instr_select_vars(ast.node)
	elif isinstance(ast, Stmt):
		return sum(map(instr_select_vars, ast.nodes),[])
	elif isinstance(ast, Printnl):
		return  [Push86(instr_select_vars(ast.nodes[0])), Call86('print_int_nl'), Add86(Const86(4),ESP)]
	elif isinstance(ast, Assign):
		if isinstance(ast.expr, Add):
			expr_setup = [Move86(instr_select_vars(ast.expr.left), Var(ast.nodes[0].name,-1))]
			return expr_setup + [Add86(instr_select_vars(ast.expr.right), Var(ast.nodes[0].name,-1))]
		elif isinstance(ast.expr, UnarySub):
			expr_setup = [Move86(instr_select_vars(ast.expr.expr), Var(ast.nodes[0].name,-1))]
			return expr_setup + [Neg86(Var(ast.nodes[0].name,-1))]
		elif isinstance(ast.expr, CallFunc):
			expr_setup = instr_select_vars(ast.expr)
			return expr_setup + [Move86(EAX, Var(ast.nodes[0].name,-1))]
		else:
			return [Move86(instr_select_vars(ast.expr), Var(ast.nodes[0].name,-1))]
	elif isinstance(ast, CallFunc):
		return [Call86('input')]
	elif isinstance(ast, Const):
		return Const86(ast.value)
	elif isinstance(ast, Name):
		return Var(ast.name,-1)
	elif isinstance(ast, AssName):
		return []
	else:
		raise Exception("Unexpected term: " + str(ast))


def liveness_analysis(instr_list):
	liveness = [Live_vars(set([]),set([])),]
	print liveness[0]
	# liveness[0].add_before(set([3,3,3,4,4,4]))
	# print liveness[0]
	# liveness.append(Live_vars(set([1,2,2,3,4]), set([5,5,6,7,7,8])))
	# print liveness[1]
	for i in range (0,3):#(0,len(instr_list)):
		print i
		liveness[i].add_before(set([i,i]))
		liveness.append(Live_vars(set([]),liveness[i].before))
		print liveness[i]
	liveness.reverse()
	print '\n\n'
	for n in liveness:
		print n
	return liveness


def add_header_footer_x86(instructions, number_of_stack_vars, value_mode=Move86):
	return [Push86(EBP), Move86(ESP, EBP), Sub86(Const86(number_of_stack_vars * 4), ESP)] + instructions + [Move86(Const86(0), EAX), Leave86(), Ret86()]


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

	#print inputFile
	ast = compiler.parseFile(inputFile);
	if(print_stmts):
		print 'compile'+inputFilePath
	#ast = parse_file(inputFilePath);

	if(print_stmts):
		print ast, '\n\n\n'
	fast = flatten(ast)

	print 'flatten(ast)\n',fast,'\n'
	if(print_stmts):
		print fast
	assembly = instr_select_vars(fast)
	for i in assembly:
		print i
	print map(str, assembly)

	liveness_analysis(assembly)

	#write_to_file(map(str, assembly), outputFileName)

	return 0

if __name__ == '__main__':
	main();

