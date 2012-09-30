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
#from parse import parse_file


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
EBX = Reg86('ebx')
ECX = Reg86('ecx')
EDX = Reg86('edx')
ESI = Reg86('esi')
EDI = Reg86('edi')

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

def get_written_vars(instr):
	l = []
	if isinstance(instr, Move86) or isinstance(instr,Add86) or isinstance(instr, Neg86):
		if isinstance(instr.target, Var):
			l.append(instr.target.name)	
	return l

def get_read_vars(instr):
	l = []
	if isinstance(instr, Push86) or isinstance(instr, Move86) or isinstance(instr, Add86):
		if isinstance(instr.value, Var):
			l.append(instr.value.name)
	if isinstance(instr, Add86) or isinstance(instr, Neg86):
		if isinstance(instr.target, Var):
			l.append(instr.target.name)
	return l

def liveness_analysis(instr_list):
	liveness = [Live_vars(set([]),set([])),]
	for i in range(0,len(instr_list)-1):
		instr_list_i = len(instr_list)-1-i
		w_var = get_written_vars(instr_list[instr_list_i])
		r_var = get_read_vars(instr_list[instr_list_i])
		before = (liveness[i].after - set(w_var)) 
		before = before | set(r_var)
		liveness[i].add_before(before)
		liveness.append(Live_vars(set([]),liveness[i].before))
		# print i,map(str,liveness[i].before),map(str,liveness[i].after)
	liveness.reverse()

	print '\n\nLiveness'
	for n in liveness:
		print map(str,n.after)
	return liveness

def initialize_intrf_graph(live_list):
	var_list = set([])
	for n in live_list:
		var_list = n.after | var_list
	print var_list
	graph = {}
	for n in var_list:
		graph[n] = set([])
	print graph
	return graph

def create_intrf_graph(instr_list, live_list):
	interference_graph = initialize_intrf_graph(live_list)
	for i in range(0, len(instr_list)-1):
		instr = instr_list[i]
		live_after = live_list[i].after
		if (isinstance(instr, Move86) and (isinstance(instr.target, Var) or isinstance(instr.target, Reg86))):
			#interference_graph[instr.target.name] = set([])
			if instr.target.name in live_after:
				for v in live_after:
					if v != instr.target.name:
						if instr.target.name in interference_graph:
							interference_graph[instr.target.name] = set([v]) | set(interference_graph[instr.target.name])
						else:
							interference_graph[instr.target.name] = set([v])
						if v in interference_graph:
							interference_graph[v] = set([instr.target.name]) | set(interference_graph[v])
						else:
							interference_graph[v] = set([instr.target.name])
		if (isinstance(instr, Add86) or isinstance(instr, Neg86) and (isinstance(instr.target, Var) or isinstance(instr.target, Reg86))):
			for v in live_list[i].after:
				if(v != instr.target.name):
					if instr.target.name in interference_graph:
						interference_graph[instr.target.name] = set([v]) | interference_graph[instr.target.name]
					else:
						interference_graph[instr.target.name] = set([v])
					if v in interference_graph:
						interference_graph[v] = set([instr.target.name]) | interference_graph[v]
					else:
						interference_graph[v] = set([instr.target.name])
		if isinstance(instr, Call86):
			print 'CALL'

			for v in live_list[i].after:
				if 'eax' in interference_graph:
					interference_graph['eax'] = set([v]) | interference_graph['eax']
				else:
					interference_graph['eax'] = set([v])
				if 'ecx' in interference_graph:
					interference_graph['ecx'] = set([v]) | interference_graph['ecx']
				else:
					interference_graph['ecx'] = set([v])
				if 'edx' in interference_graph:
					interference_graph['edx'] = set([v]) | interference_graph['edx']
				else:
					interference_graph['edx'] = set([v])
				if v in interference_graph:
					interference_graph[v] = set(['eax','ecx','edx']) | interference_graph[v]
				else:
					interference_graph[v] = set(['eax','ecx','edx'])					

	print '\n\nInterference Graph'
	for key in interference_graph:
		print key,":",map(str,interference_graph[key])
	return interference_graph

# def node_saturation(node):


def new_saturation_table(graph):
	sat_tbl = []
	for key in graph:
		sat_tbl.append([0, key])
	return sat_tbl

def update_saturation_table(sat_tbl, graph, color_tbl):
	for n in sat_tbl:
		sat = 0
		for i in graph[n[1]]:
			if(color_tbl.tbl[i]) >= 0:
				sat += 1
		n[0] = sat
	return sat_tbl

def new_color_adj_list(graph, color_tbl):
	adj = {}
	for key in graph:
		adj[key] = map(color_tbl.get_color, graph[key])
	return adj

def graph_coloring(graph):
	color_set = [0,1,2,3,4,5]
	w = graph.keys()

	color_tbl = ColorTable(graph)
	sat_tbl = new_saturation_table(graph)
	color_adj = new_color_adj_list(graph, color_tbl)
	#print color_tbl
	#print color_adj
	
	n = 0
	while len(w) != 0 :
		#print 'w',w
		current = len(w) - 1
		sat_tbl = update_saturation_table(sat_tbl, graph, color_tbl)
		sat_tbl.sort
		color_adj = new_color_adj_list(graph, color_tbl)
		#print sat_tbl
		#print color_adj
		color = min(set(color_set)-set(color_adj[w[current]]))
		#print 'color',color
		#update color table
		color_tbl.set_color(w[current],color)
		w.remove(w[current])
		#print 'w',w
		n += 1
	print '\n\nColor Table'
	for i in color_tbl.tbl:
		print str(i)+":"+str(color_tbl.tbl[i])
	return color_tbl


def add_header_footer_x86(instructions, number_of_stack_vars, value_mode=Move86):
	return [Push86(EBP), Move86(ESP, EBP), Sub86(Const86(number_of_stack_vars * 4), ESP)] + instructions + [Move86(Const86(0), EAX), Leave86(), Ret86()]

def choose_register(c):
	if c == 0:
		return EBX
	elif c == 1:
		return ESI
	elif c == 2:
		return EDI
	elif c == 3:
		return EAX
	elif c == 4:
		return ECX
	elif c == 5:
		return EDX
	else:
		raise Exception("Unexpected register: " + c)

def assign_homes(ass1, color_tbl):
	for i in ass1:
		if isinstance(i, Move86) or isinstance(i, Add86):
			if isinstance(i.value, Var):
				i.value = Reg86(choose_register(color_tbl.get_color(i.value.name)))
			if isinstance(i.target, Var):
				print i.target.name
				i.target = Reg86(choose_register(color_tbl.get_color(i.target.name)))
				print i.target
		if isinstance(i, Neg86):
			if isinstance(i.target, Var):
				i.target = Reg86(choose_register(color_tbl.get_color(i.target.name)))
		if isinstance(i, Push86):
			if isinstance(i.value, Var):
				i.value = Reg86(choose_register(color_tbl.get_color(i.value.name)))

	assembly = add_header_footer_x86(ass1,0)
	return assembly
			 
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
	ast = compiler.parseFile(inputFile)
	print ast
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

	liveness = liveness_analysis(assembly)
	intrf_graph = create_intrf_graph(assembly, liveness)
	color_table = graph_coloring(intrf_graph)

	assembly_final = assign_homes(assembly, color_table)
	print map(str,assembly_final)
	write_to_file(map(str, assembly_final), outputFileName)
	return 0

if __name__ == '__main__':
	main();

