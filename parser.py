import string

class Parser:

	def __init__(self, parser_object_fn):
		self.findArgument = parser_object_fn["argument"]
		self.findString = parser_object_fn["string"]
		self.findInteger = parser_object_fn["integer"]
		self.findVariable = parser_object_fn["variable"]

		self.variable_start = string.lowercase + "_"

	def parse(self, args):
		
		while args:
			args = args.strip()
			if args[0] == ";":
				args = self.__parse_comment(args)
			elif args[0] == "(":
				args = self.__parse_call(args)
			elif args[0] == "\"":
				args = self.__parse_string(args)
			# If variable (or function), first character must be a letter or underscore
			elif args[0].lower() in self.variable_start:
				args = self.__parse_var(args)			
			else:
				args = self.__parse_int(args)

	def __parse_comment(self, args):
		stop = args.find("\n") + 1 # stop on
		if stop: # the rest of file is a comment
			return args[stop:]
		return None


	def __parse_call(self, args):
		count = 1
		i = 1
		while count:
			if args[i] == ")":
				count -= 1
			elif args[i] == "(":
				count += 1
			i +=1
			
		if count:
			raise Exception("Incompatible parenthesis")

		expression = args[1:i-1] ## add 1 2

		self.findArgument(expression)

		return args[i:] ## ends on empty string
	

	def __parse_string(self, args):
		i = 0
		while True:
			i +=1
			if args[i] == "\"":
				break

		self.findString(args[1:i])
		return args[i+1:]


	def __parse_int(self, args):
		int_arg = args.split(" ",1)[0]
			
		self.findInteger(int_arg)

		if len(args.split(" ", 1)) <= 1:
			return None
		return args.split(" ", 1)[1]


	def __parse_var(self, args):
		arg_and_more = args.split(" ", 1) 
		self.findVariable(arg_and_more[0])

		if len(arg_and_more) <= 1:
			return None
		return arg_and_more[1]
