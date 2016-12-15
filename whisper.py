from argument import Argument

if __name__ == '__main__':
	import sys

	if len(sys.argv) != 2:
		sys.exit(1)

	with open(sys.argv[1]) as f:
		print Argument(f.read()).compile()

