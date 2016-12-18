import re

import wp.template
from wp.parser import Parser
from scope import Scope
from wp.types import ctypes
from wp import template

def argchecker(fn):
    	"""
		Decorator called from within operations to discover 
		the local variables' types of function parameters for a scope's function definition
		Checks:
			- all args have the same type (or some have NONE)
			- atleast 1 argument has a type (other can have NONE)
	"""
	def _get_type(args):
		#Get the return type of the arguments
		_type = None
 		for arg in args:
 			if arg.type() == ctypes.NONE:
 				continue
 			if _type and _type != arg.type():
 				raise Exception("Comparison between different type variables")
 			_type = arg.type()
		return _type


	def inner(self):
		_type = _get_type(self.all_args)
 		if _type == ctypes.NONE:
 			raise Exception("Comparison With Unknown variables")

 		for arg in self.all_args:
 			if arg.type() == ctypes.NONE:
 				var = self.scope.get_variable(arg.compile()) # argument is stored in the scope 
 				self.scope.add(arg.compile(), _type, var.value) # we need its value

 		return fn(self)

	
 	return inner



class Argument:
	def __init__(self, args, scope=Scope()):
		self.callable = False
		self.all_args = []

		self.scope = scope 

		parser = Parser({
			"string" : self.find_str,
			"integer" : self.find_int,
			"variable": self.find_var,
			"argument" : self.find_arg, 
		})
		parser.parse(args)


	def execute(self):
		return self.all_args[0].execute()

	def compile(self):
		main = 	("#include <stdio.h>\n"
				 "#include <string.h>\n"
				 "#include \"lisp_def.c\"\n\n"
				 "//prototype definitions\n"
				 "{{}}\n\n"
				 "//variable definitions\n"
				 "{{}}\n\n"
				 "//function definitions\n"
				 "{{}}\n\n" 
				 "int main() {{{{\n"
				 "\t{};\n"
				 "\treturn 0;\n"
				"}}}}")
		calls = []
		for arg in self.all_args:	
			calls.append(arg.compile(call=True) if arg.callable else arg.compile())

		main_code = main.format(';\n'.join(calls))	

		fns = self.scope.compile_functions()

		main_code = main_code.format('\n'.join(self.scope.protos),
										self.scope.compile_variables(),
										fns)
		return main_code

	def getArgumentClass(self, id_str):
		argument_types = {
			"neg": NegArgument,
			"add": AddArgument,
			"sub": SubArgument,
			"mul": MulArgument,
			"div": DivArgument,
			"mod": ModArgument,
			"lt": LtArgument,
			"le": LeArgument,
			"ge": GeArgument,
			"gt": GtArgument,
			"eq": EqArgument,
			"ne": NeArgument,
			"not": NotArgument,
			"and": AndArgument,
			"or": OrAgument,
			"set": SetArgument,
			"seq": SeqArgument,
			"print": PrintArgument,
			"readi": ReadiArgument,
			"reads": ReadsArgument,
			"if": IfArgument,
			"while": WhileArgument,
			"def": DefArgument,
		}
		if argument_types.has_key(id_str):
			return lambda s: argument_types[id_str](s, scope=self.scope)
 
		if self.scope.get_scope(id_str):
			return lambda s: FunctionCallArgument(s, scope=self.scope, name=id_str)
			
		raise Exception("Identifier '{}' not found.".format(repr(id_str)))


	def find_arg(self, expression):
		"""
			Function given by the Argument to the parser, 
			defining how it procedes, when it finds a special name.

			Special case:
				
				It can be the parameter part of a function definition: "(def function (a) a)""
	
				In this case, "a" is a parameter, but the parser sees "a" as a function, call.
				The compiler notices this case and doesn't process it.

			If it isn't the special case, we try and find the function to call

		"""
		clean_expression = re.sub("\t|\n"," ", expression)
		if isinstance(self, DefArgument) and len(self.all_args) == 1:
			#arg = ([name] + parameters) if name else []
			if clean_expression.strip():
				arg = clean_expression.split(" ")
			else:
				arg = []
		else:
			function_call = clean_expression.split(" ",1)
			name, parameters = function_call if len(function_call) > 1 else (function_call[0], None)

			call_class = self.getArgumentClass(name)
			arg = call_class(parameters if parameters else None)

		self.all_args.append(arg)

	def find_var(self, arg):
		var = VarArgument(arg, self.scope)
		if isinstance(self, DefArgument) and len(self.all_args) == 0: 
			self.scope = Scope(name=var.arg, scope=self.scope)

		self.all_args.append(var)

	def find_int(self, int_arg):
		self.all_args.append(IntegerArgument(int_arg))

	def find_str(self, string):
		self.all_args.append(StringArgument(string))

class AddArgument(Argument):
	def execute(self):

		args = []
		for arg in self.all_args:
			args.append(arg.execute())

		return sum(args)

	@argchecker
	def compile(self):
		return "({})".format(" + ".join(arg.compile() for arg in self.all_args))

	def type(self):
		return ctypes.INT

class SubArgument(Argument):
	def execute(self):
		args = [arg.execute() for arg in self.all_args]
		return reduce(lambda a,b: a-b, args)

	@argchecker
	def compile(self):
		return "({})".format(" - ".join(arg.compile() for arg in self.all_args))
	def type(self):
		return ctypes.INT

class VarArgument(Argument):
	def __init__(self, s, scope):
		self.scope = scope
		self.arg = s
		self.callable = False

	def compile(self):
		return  str(self.arg)

	def execute(self):
		return self.scope[self.arg]

	def set(self, val):
		self.scope[self.arg] = val 

	def type(self):
		return self.scope.get_variable(self.compile()).ctype


class IntegerArgument(Argument):
	def __init__(self, s, *args, **kwargs):
		self.callable = False
		self.val = int(s)

	def execute(self):
		return self.val

	def compile(self):
		return str(self.val)

	def type(self):
		return ctypes.INT

class StringArgument(Argument):
	def __init__(self, s, *args, **kwargs):
		self.callable = False
		#Argument.__init__(self,s) -> doesnt perform parsing
		self.string = s

	def execute(self):
		return self.string

	def compile(self):
		return "\"{}\"".format(self.string)

	def type(self):
		return ctypes.STRING

class SeqArgument(Argument):
	def __init__(self,*args, **kwargs):
		Argument.__init__(self, *args, **kwargs)
		self.callable = True

	def execute(self):
		args = [arg.execute() for arg in self.all_args]
		return args[-1]

	def compile(self, call=False):
		def mapfn(arg):
			return (arg.compile(call=True) if arg.callable else arg.compile()) + ";"

		seq_calls = map(mapfn, self.all_args)

		if  self.all_args[-1].type() != ctypes.VOID:
			seq_calls[-1] = "return {}".format(seq_calls[-1])

		fn_call = self.scope.new_function('\n'.join(seq_calls), type=self.type())
		return "{}()".format(fn_call) if call else fn_call 


	def type(self):
		map(lambda arg: arg.type(), self.all_args[:-1])
		return self.all_args[-1].type()


class WhileArgument(Argument):
	def execute(self):
		conditional = self.all_args[0]
		while True:
			val = conditional.execute()
			if not val:
				return val
			self.all_args[1].execute()

	def compile(self):
		whiles ="""while ({}) {{{};}}"""
		
		check = self.all_args[0].compile(call=True)\
				if self.all_args[0].callable else self.all_args[0].compile()
		body = self.all_args[1].compile(call=True)\
				if self.all_args[1].callable else self.all_args[1].compile()
		return whiles.format(check, body)

	def type(self):
		return ctypes.INT


class EqArgument(Argument):
	def execute(self):
		return int(self.all_args[0].execute() == self.all_args[1].execute())
	def type(self):
		return ctypes.INT
	def compile(self):
		eq = "({})".format(self.all_args[0].compile())
		for arg in self.all_args[1:]:
			eq = "({} == {})".format(eq, arg.compile())
		return eq

class NeArgument(Argument):
	def execute(self):
		return int(self.all_args[0].execute() != self.all_args[1].execute())
	def type(self):
		return ctypes.INT
	def compile(self):
		ne = "({})".format(self.all_args[0].compile())
		for arg in self.all_args[1:]:
			ne = "({} != {})".format(ne, arg.compile())
		return ne


class NegArgument(Argument):
	def execute(self):
		return -self.all_args[0].execute()

	def compile(self):
		return "-{}".format(self.all_args[0].compile())

	def type(self):
		return ctypes.INT


class SetArgument(Argument):
	def execute(self):
		self.all_args[0].set(self.all_args[1].execute())
	
	def compile(self):
		if not self.scope.in_compilation_scope:
			raise Exception("No scope being compiled, can't set the scope")
		return self.scope.in_compilation_scope.new_variable(self.all_args[0].compile(),
										self.all_args[1].type(),
										self.all_args[1].compile()) # is this callable??

	def type(self):
		if not self.scope.in_compilation_scope:
			raise Exception("No scope being compiled, can't set the scope")
		self.scope.in_compilation_scope.new_variable(self.all_args[0].compile(),
										self.all_args[1].type(),
										None)
		return self.all_args[1].type()
		#return ctypes.VOID


class PrintArgument(Argument):
	def __init__(self, *args, **kwargs):
		Argument.__init__(self, *args, **kwargs);
		self.callable = True
	def execute(self):
		args = [str(arg.execute()) for arg in self.all_args]
		print ' '.join(args)
		return args[-1]

	def compile(self, call=False):

		type_formatters = []

		print_args = [arg.compile() for arg in self.all_args]

		for arg in self.all_args:

			if arg.type() == ctypes.STRING:
				type_formatters.append("%s")
			else:
				type_formatters.append("%d")



		prints = "printf(\"{}\\n\",{});".format(" ".join(type_formatters),\
		  ", ".join(print_args))

		fn_call = self.scope.new_function(prints)
		return "{}()".format(fn_call) if call else fn_call 

	def type(self):
		return ctypes.VOID

class IfArgument(Argument):
	def execute(self):	
		if self.all_args[0].execute():
			return self.all_args[1].execute()
		return self.all_args[2].execute()

	def compile(self):

		if self.all_args[0].type() != ctypes.INT:
			raise Exception("Condition must return true value");

		if_type = self.all_args[1].type()

		if if_type != self.all_args[2].type():
			raise Exception("If branches must have same return value")

		
		fn_arg_str = "({},{},{})".format(*[arg.compile() for arg in self.all_args])

		if if_type == ctypes.VOID: 
			if_type_fn_str = "__if_val_fn_void{}".format(fn_arg_str)

		elif if_type == ctypes.INT: 
			if_type_fn_str = "__if_val_int{}".format(fn_arg_str)

		elif if_type == ctypes.STRING:
			if_type_fn_str = "__if_ref_char{}".format(fn_arg_str)

		#global_fns.append(if_type_fn_str) 

		return if_type_fn_str


	def type(self):
		return ctypes.INT


class NotArgument(Argument):
	def execute(self):
		return not self.all_args[0].execute()

	def compile(self):
		return "! ({})".format(self.all_args[0].compile())

	def type(self):
		return ctypes.INT

class MulArgument(Argument):
	def execute(self):
		args = [arg.execute() for arg in self.all_args]
		return reduce(lambda a,b: a*b, args, 1)

	def type(self):
		return ctypes.INT

	@argchecker	
	def compile(self):
		return "({})".format(" * ".join(arg.compile() for arg in self.all_args))


class DivArgument(Argument):
	def execute(self):
		args = [arg.execute() for arg in self.all_args]
		return args[0] / args[1]
	def type(self):
		return ctypes.INT

	@argchecker
	def compile(self):
		return "({})".format(" / ".join(arg.compile() for arg in self.all_args))


class ModArgument(Argument):
	def execute(self):
		args = [arg.execute() for arg in self.all_args]
		return args[0] % args[1]
	def type(self):
		return ctypes.INT

	@argchecker
	def compile(self):
		return "({})".format(" % ".join(arg.compile() for arg in self.all_args))


class LtArgument(Argument):
	def execute(self):
		return int(self.all_args[0].execute() < self.all_args[1].execute())
	def type(self):
		return ctypes.INT

	@argchecker
	def compile(self):
		return "({} < {})".format(self.all_args[0].compile(), self.all_args[1].compile())


class LeArgument(Argument):
	def execute(self):
		return int(self.all_args[0].execute() <= self.all_args[1].execute())
	def type(self):
 		return ctypes.INT

 	@argchecker
 	def compile(self):
		return "({} <= {})".format(self.all_args[0].compile(), self.all_args[1].compile())



class GeArgument(Argument):
	def execute(self):
		return int(self.all_args[0].execute() >= self.all_args[1].execute())
	def type(self):
		return ctypes.INT

	@argchecker
	def compile(self):
		return "({} >= {})".format(self.all_args[0].compile(), self.all_args[1].compile())



class GtArgument(Argument):
	def execute(self):
		return int(self.all_args[0].execute() > self.all_args[1].execute())
	def type(self):
		return ctypes.INT
	@argchecker
	def compile(self):
		return "({} > {})".format(self.all_args[0].compile(), self.all_args[1].compile())


 
class AndArgument(Argument):
	def execute(self):
		return int(self.all_args[0].execute() and self.all_args[1].execute())
 	def type(self):
 		return ctypes.INT
 	@argchecker
 	def compile(self):
		return "({} && {})".format(self.all_args[0].compile(), self.all_args[1].compile())



class OrAgument(Argument):
	def execute(self):
		return int(self.all_args[0].execute() or self.all_args[1].execute())
	def type(self):
		return ctypes.INT

	@argchecker
	def compile(self):
		return "({} || {})".format(self.all_args[0].compile(), self.all_args[1].compile())

 
class ReadiArgument(Argument):
	def execute(self):
		return int(raw_input())
	def type(self):
		return ctypes.INT
	def compile(self):
		readi="""
			scanf(\"\%d\", &__tmp_int__);
		"""
		# i have to change this to a __builtin__input__function which returns the value directly
		return "()"

class ReadsArgument(Argument):
	def execute(self):
		return raw_input()
	def type(self):
		return ctypes.STRING

	def compile(self):
		#same problem as above
		return "()"


class DefArgument(Argument):
	def __init__(self, *args, **kwargs):

		Argument.__init__(self, *args, **kwargs)

		for var in self.all_args[1]:
			self.scope.new_parameter(var)#VarArgument(var, scope=self.scope).compile())

		function = self.all_args[2]
		self.scope.new_scope_function(function)

	
	def compile(self):
		return ""

	def type(self):
		return self.all_args[2].type()


class FunctionCallArgument(Argument):
	def __init__(self, *args, **kwargs):
		#quick hack
		self.fn_name = kwargs.pop("name")

		Argument.__init__(self, *args, **kwargs)

	def compile(self):
		fn_name = self.scope.get_scope(self.fn_name).call(self.all_args)
		return template.functionCall(fn_name, [arg.compile() for arg in self.all_args])

	def type(self):
		scope = self.scope.get_scope(self.fn_name).call(self.all_args)
		return scope.type()

class CFunctionCallArgument(Argument):
	def __init__(self, *args, **kwargs):
		self.fn_name = kwargs.pop("name")
		Argument.__init__(self, *args, **kwargs)


	def compile(self):
		args = [arg.compile(call=True) if arg.callable else arg.compile()\
					 for arg in self.all_args ] 
		return "{}({})".format(self.fn_name, ','.join(args))

	def type(self):
		return creturns[self.fn_name]
