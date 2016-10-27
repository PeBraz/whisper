import string
import re
from collections import namedtuple
from collections import OrderedDict


CType = namedtuple('CType', ['STRING', 'INT', 'VOID', 'NONE'])
ctypes = CType(
	NONE=0,
	STRING="char*",
	INT="int",
	VOID="void"
)

def argchecker(fn):
	"""
		Decorator called from within operations to discover 
		the local variables' types of function parameters for a scope's function definition
		Checks:
			- all args have the same type (or some have NONE)
			- atleast 1 argument has a type (other can have NONE)
	"""
	def inner(self):
		compare_type = None
 		for arg in self.all_args:
 			if arg.type() == ctypes.NONE:
 				continue
 			if compare_type and compare_type != arg.type():
 				raise Exception("Comparison between different type variables")
 			compare_type = arg.type()

 		if compare_type == ctypes.NONE:
 			raise Exception("Comparison With Unknown variables")

 		for arg in self.all_args:
 			if arg.type() == ctypes.NONE:
 				scope_variable = self.scope.get_variable(arg.compile()) # argument is stored in the scope 
 				self.scope.set_local(arg.compile(), compare_type, scope_variable.value) # we need its value
 		return fn(self)
 	return inner

class ScopeVariable:
	"""
		@optional 	value 	the value used for the variable initialization, 
							if None given, use ctype specific initialization value
	"""
	def __init__(self, name, ctype, value=None, size=0):
		self.name = name
		self.identifier = name.split('.')[-1]
		self.ctype = ctype

		if value:
			self.value = value
		elif ctype == ctypes.STRING:
			self.value = ""
		elif ctype == ctypes.INT:
			self.value = 0
		else:
			raise Exception("Don't know what to assign as initial value to the type received")

		if size:
			self.size = size
		else:
			self.size = len(value) - 1 if value and ctype == ctypes.STRING  else 0

	def clone(self):
		return ScopeVariable(self.name, self.ctype, value=self.value)

class ScopeStruct:
	"""
		Defines a C structure where a scope's variables are stored
	"""
	def __init__(self, scope):
		self.args = OrderedDict() # (name: Variable())
		self.name = scope.name 
		self.template = "struct {{{}}} {};"


	def add_variable(self, variable):
		"""
			Add a variable unique to this scope, the type is important for the declaring/initializing it
		"""
		arg = self.args.get(variable.name)
		if arg:
			self.args[variable.name].ctype = variable.ctype
		else:
			self.args[variable.name] = variable
		"""
		arg = self.args.get(variable.name)	
		if (not arg):
			self.args[variable.name] = variable
		elif (arg.ctype == ctypes.NONE):
			self.args[variable.name].ctype = variable.ctype
		else:
			raise Exception("Variable is already declared in '{}' context".format(self.name))
		"""


	def get_variable(self, var_name):
		"""
			@returns 	ScopeVariable object or None
		"""
		return self.args.get(var_name)
		

	def init_var(self, var_name, value=None):
		"""
			Returns the C value assignement string for the variable with the name given,
			using its default value initialization (ex: 0 for int) or using the 'value' 
			as the right operand

			If the variable is a string, we may need to give the initial buffer a bigger size 

			@arg 		var_name	name of the variable to initialize with its 
			@optional 	value 		value to use for assignement

			@returns 	string for value assignements
		"""
		if not self.args.has_key(var_name):
			raise Exception("Variable '{}' not in scope '{}'".format(var_name, self.name))

		var = self.args[var_name]

		set_value = var.value

		if value:
			if var.ctype == ctypes.STRING:
				var.size = max(var.size, len(value)) - 1 # remove <""> and add <\0> 
			set_value = value

		if var.ctype == ctypes.NONE:
			raise Exception("Tried to initialize a value with no type")
		elif var.ctype == ctypes.STRING:
			return "memcpy({}, {}, {});\n".format(var.name, set_value, var.size)
		elif var.ctype == ctypes.INT:
			return "{} = {};".format(var.name, set_value);
		else:
			raise Exception("Who knows?")
 
	def declare_var(self, var_name):
		if not self.args.has_key(var_name):
			raise Exception("Variable '{}' not in scope '{}'".format(var_name, self.name))

		var = self.args[var_name]
		if var.ctype == ctypes.NONE: # if none type, then its value comes from a local variable
			raise Exception("Tried to initialize a value with no type")
		elif var.ctype == ctypes.STRING:
			return "{} {}[{}];".format("char", var.identifier, var.size)
		else:
			return "{} {};".format(var.ctype, var.identifier);


	def init_all_var(self):
		return '\n'.join(self.init_var(var) for var in self.args)

	def declare_all_var(self):

		return '\n'.join(self.declare_var(var) for var in self.args)


	def create(self):
		"""
			Create the structure associated with this scope
		"""
		return self.template.format(self.declare_all_var(), "__" + self.name)



class ScopeFunction:

	class FunctionType:
		def __init__(self, params, ret):
			self.params = params
			self.ret = ret

		def set_name(self, name):
			self.name = name

		def __eq__(self, other):
			"""
				Two scope functions are equal if they have arguments and return value of equal types 
			"""
			return self.ret == other.ret and self.args == other.args

	def __init__(self, scope):
		self.args = OrderedDict() # (ctype, str)
		self.name = scope.name
		self.functions = [] # Stores function types
		self.body = None
		self.scope = scope
		self.this_counter = 0

	def __eq__(self, other):
		"""
			Two scope functions are equal if they have arguments and return value of equal types 
		"""
		return self.ret == other.ret and self.args == other.args

	def add_arg(self, name, ctype):
		# if the arg doesnt exist or is none, update
		arg = self.args.get(name)	
		if (not arg) or (arg == ctypes.NONE):
			self.args[name] = ctype

	def set_body(self, body):
		self.body = body

	def create(self):
		if not self.body:
			raise Exception("The scope function '{}' has no body!!".format(self.name))

		fn_template = "{} {} ({}) {{{};}}"
		args = ["{} {}".format(var.ctype, var.identifier) for var in self.scope.params.values()]
		body = "{}\n{} {}".format(self.scope.scope_struct.init_all_var(),\
			"return" if self.scope.ret != ctypes.VOID else "",\
		 self.body.compile(call=True) if self.body.callable else self.body.compile())

		self.scope.protos.append("{} {} ({});".format(self.scope.ret, self.scope.call_name,','.join(args)))
		return fn_template.format(self.scope.ret, self.scope.call_name, ','.join(args), body)

class Scope:

	def __init__(self, name="main", scope=None):
		## add this scope to father scope
		self.name = name
		if scope:
			scope.add_scope(self)

		self.father = scope

		self.fullname = "{}_{}".format(scope.fullname, name) if scope else name

		self.call_name = None
		self.ctype = ctypes.NONE

		# this scope gets transformed into a function and a struct
		# more than 1 of each is possible, if one argument can have multiple types
		#self.cfunctions = []
		self.scope_function = ScopeFunction(self)
		self.scope_struct = ScopeStruct(self)
		self.other_scopes = []

		self.params = None
		self.ret = None
		self.original_name = self.name

		self.fn_counter = 0
		self.scope_counter = 0
		self.functions = scope.functions if scope else [] 
		self.protos = scope.protos if scope else []

		self.fn_name_template = "__fn_{scope}_{id}"
		self.fn_template = "{type} {name}(){{{body};}}"

		self.scopes = OrderedDict() # Child Scopes

		self.in_compilation_scope = None

	def add_scope(self, scope):
		"""
			add_scope - adds a new scope, as a child
						this way, from the father you can reach a scope function directly
			@arg scope 		scope object
		"""
		self.scopes[scope.name] = scope

	def set_call(self, fn_name):
		"""
			set_call - the function name given, directs to the function the scope uses directly 
			@arg fn_name 	name of the function of this scope
		"""
		self.call_name = fn_name

	def get_scope(self, name):
		scope = self
		while scope:
			s = scope.scopes.get(name)
			if s:
				return s 
			scope = scope.father


	def new_scope_function(self, fnArgument):
		"""
			Receives an fnArgument for an object it can't .compile() yet, 
			This function's parameters may have more than 1 type, and it needs to find their types
			
			@fnArgument 	Argument object that represents the function to be called
			@returns 	the name of the function that is going to be created
		"""

		self.scope_function.set_body(fnArgument)

	def set_local(self, local_name, local_type, local_value):
		self.scope_struct.add_variable(ScopeVariable(local_name, local_type, value=local_value))
		self.scope_function.add_arg(local_name, local_type)


	def new_function(self, body, type=ctypes.INT):
		"""
			new_function - Creates a placeholder function, this function receives no arguments,
			@arg body   body of this function
			@arg type 	return type for the corresponding C function

			@returns  	the name of the corresponding C function that can be called
		"""
		name = self.fn_name_template.format(scope=self.fullname,id=self.fn_counter)
		self.protos.append("{} {}();".format(type, name))
		self.fn_counter += 1;
		template = self.fn_template.format(type=type, name=name,body=body)
		self.functions.append(template)
		return name

	def __complete(self):
		"""
			A complete scope can be called because it has defined variables (no ctypes.NONE)
		"""
		return  (ctypes.NONE in self.params) or (self.ret == ctypes.NONE) 

	def compile_functions(self):
		for scope in self.scopes.itervalues():
			scope.compile_functions()

		
		for scope in self.other_scopes:
			# NOTE: at scope creation, the list from father to children is shared, but not from scope to other_scopes
			
			prev_comp_scope = self.in_compilation_scope
			self.in_compilation_scope = scope
			self.functions.append(scope.scope_function.create())
			self.in_compilation_scope = prev_comp_scope
			#self.functions.extend(scope.functions)

		return '\n'.join(self.functions)

	def new_variable(self, var_name, var_type, var):
		"""
			Creates a new variable for this scope (and children) only
		"""
		# for local variables, for which the type is not known
		if not var_type: 
			self.scope_struct.add_variable(ScopeVariable(var_name, ctypes.NONE, value=var))
			self.scope_function.add_arg(var_name, ctypes.NONE)
			return 

		# for redeclarations of values
		old = self.scope_struct.get_variable(var_name)
		if old:
			#if variable has no type
			if old.ctype == ctypes.NONE:
				old.ctype = var_type
			# If using a different variable type, than declared
			elif old.ctype != var_type :
				raise Exception("Can't assign {} to declared variable of type {}"
					.format(var_type, old.ctype))

		else:
			self.scope_struct.add_variable(ScopeVariable(var_name, var_type))

		return self.scope_struct.init_var(var_name, value=var)
			
	def get_variable(self, name):
		return self.scope_struct.get_variable(name)

	def compile_variables(self):
		structs = []#self.scope_struct.create()  + "\n"

		for scope in self.other_scopes:
			structs.append(scope.scope_struct.create())# scope.compile_variables()

		for scope in self.scopes.values():
			structs.append(scope.compile_variables())

		return '\n'.join(structs)


	def new_type_scope(self, params, ret):
		"""
			Creates a new scope for specific type parameters / return value combos
		"""

		for scope in self.other_scopes:
			if scope.ret == ret and  all(a.ctype == b.ctype for a,b in zip(scope.params.values(), params.values())):
				return scope

		# create a new scope
		new_name = "{}_{}".format(self.name, self.scope_counter)
		self.scope_counter += 1

		new_scope = Scope(name=new_name, scope=self.father)
		new_scope.in_compilation_scope = self
		new_scope.call_name = new_name	

		new_scope.scope_struct.args = OrderedDict() 
		# First clean all the names on the new scope
		for var in self.scope_struct.args.itervalues():
			new_name = "__{}.{}".format(new_scope.name, var.identifier)

			param = params.get(var.name)

			this_type = param.ctype if param else var.ctype
			size = len(param.value) - 1 if param else 0
			new_scope.scope_struct.args[new_name] = ScopeVariable(new_name, this_type, var.value, size=size)


		new_scope.scope_function.args = OrderedDict(self.scope_function.args)
		new_scope.scope_function.set_body(self.scope_function.body)
		new_scope.protos = self.protos


		new_scope.ret = ret
		new_scope.params = params

		self.other_scopes.append(new_scope)
		return new_scope

	def call(self, parameters):
		"""
			Check parameters for this scope's functions
		"""

		local_args = self.scope_function.args.iteritems()
	
		fn_types = OrderedDict()
		for p in parameters:
			local_name, local_type = local_args.next()
			# if local has a type, then the type of the parameter must be the same
			if local_type != ctypes.NONE and local_type != p.type():
				raise Exception("Expected argument of type '{}' received '{}'".format(local_type, p.type()))

			fn_types[local_name] = ScopeVariable(local_name, p.type(), value=p.compile()) 


		
		# Now all function parameters are confirmed

		# temporarily make types in the functions be the same to the function  (instead of ctypes.NONE)
		#there is no problem changing them here to whatever the FunctionType tells us to

		## Create a temporary score to perform temporary variable changes for this compilation 
		tmp_scope_struct = OrderedDict()
		struct = self.scope_struct.args 
		for var in fn_types.values():
			tmp_scope_struct[var.name] = var


		self.scope_struct.args = tmp_scope_struct

		ret = self.scope_function.body.type()
		self.scope_struct.args = struct
		return self.new_type_scope(fn_types, ret)

	def type(self):
		if self.ret == None:
			raise Exception("Function type is unknown, compile it first")
		return self.ret

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
			# If variable, first character must be a letter or underscore
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
		#if self.all_args[0].callable:
		#	main_code = main.format(self.all_args[0].compile(call=True))
		#else:
	#		main_code = main.format(self.all_args[0].compile())


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
 		# its a user defined scope
 		# go up the scopes until 'main' to find the scope

 
		if self.scope.get_scope(id_str):
			return lambda s: FunctionCallArgument(s, scope=self.scope, name=id_str)
			
		raise Exception("Identifier '{}' not found.".format(repr(id_str)))


	def find_arg(self, expression):
		"""
			Function given by the Argument to the parser, 
			defining how it procedes, when it finds a special name
		"""
		clean_expression = re.sub("\t|\n"," ", expression)
		if isinstance(self, DefArgument) and len(self.all_args) == 1:

			#arg = ([name] + parameters) if name else []
			arg = clean_expression.split(" ")
		else:
			name, parameters = clean_expression.split(" ",1)

			call_class = self.getArgumentClass(name)
			arg = call_class(parameters if len(parameters) else None)

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
		scope = self.scope.in_compilation_scope or self.scope 
		return "__{}.{}".format(scope.name, str(self.arg))

	def execute(self):
		return self.scope[self.arg]

	def set(self, val):
		self.scope[self.arg] = val 

	def type(self):
		scope = self.scope.in_compilation_scope or self.scope
		return scope.get_variable(self.compile()).ctype


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
		return self.scope.new_variable(self.all_args[0].compile(),
										self.all_args[1].type(),
										self.all_args[1].compile()) # is this callable??

	def type(self):
		return ctypes.VOID


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

		for var in self.all_args[1]: # function variables, these have ctype.None
		 	# add the arguments in order, they can only be declared after their types are known
			self.scope.new_variable(VarArgument(var, scope=self.scope).compile(), None, var)

		function = self.all_args[2]
		
		call_name =\
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
		fn_scope = self.scope.get_scope(self.fn_name)

		self.scope = fn_scope.call(self.all_args)
		return "{}({})\n".format(self.scope.name, ','.join(arg.compile() for arg in self.all_args))

	def type(self):
		fn_scope = self.scope.get_scope(self.fn_name)
		scope = fn_scope.call(self.all_args)
		return scope.type()


if __name__ == '__main__':
	import sys

	if len(sys.argv) != 2:
		sys.exit(1)

	with open(sys.argv[1]) as f:
		print Argument(f.read()).compile()

