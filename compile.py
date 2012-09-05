#compile.py

# Anne Gatchell
# CSCI 5525

"""
Usage: compile.py <file_name>

"""

import sys
import compiler



def main():
	if(len(sys.argv) != 2):
		print 'Usage: compile.py <file_name>'
		return 1;
	print 'hello there,', sys.argv[1]
	inputFile = sys.argv[1]
	ast = compiler.parseFile(inputFile);

	print ast



if __name__ == '__main__':
	main();