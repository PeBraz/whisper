from collections import OrderedDict

from wp.types import ctypes


class ScopeVariable:
	"""
		Creates a variable inside a ScopeVariable
		
		- the 'mutalbe' property defines it that variable can be changed (to have different types)
			- if has type ctypes.NONE then it is 'mutable' and can be changed

		@name 		the name of the variable in the scope 
		@ctype 		(optional) the type of the scope
		@value 		(optional) the value used for the variable initialization, 
					if None given, use ctype specific initialization value
	"""

	@staticmethod
	def create(name, ctype=ctypes.NONE, value=None):
		if ctype == ctypes.STRING:
			return StringVariable(name, value=value)
		elif ctype == ctypes.INT:
			return PrimitiveVariable(name, ctype=ctype, value=value)
		else:
			return NoneVariable(name)

	def init(self, scope_name):
		pass
	def declare(self):
		pass
	def clone(self):
		pass

class NoneVariable(ScopeVariable):
	def __init__(self, name):
		self.name = name
		self.ctype = ctypes.NONE

	def init(self, scope_name):
		raise Exception("Tried to initialize value '{}' with no type".format(self.name))
	def declare(self):
		raise Exception("Tried to declare value '{}' with no type".format(self.name))
	def clone(self):
		return NoneVariable(self.name)

class PrimitiveVariable(ScopeVariable):
	def __init__(self, name, ctype=None, value=None):
		if not ctype:
			raise Exception("Tried to initialize a primitive variable {} with no type.".format(name))
		self.name = name
		self.value = value if value else 0
		self.ctype = ctype

	def init(self, scope_name):
		return  "__{}.{} = {};".format(scope_name, self.name, self.value)

	def declare(self):
		return "{} {};".format(self.ctype, self.name);
	def clone(self):
		return PrimitiveVariable(self.name, ctype=self.ctype, value=self.value)

class StringVariable(ScopeVariable):
	def __init__(self, name, ctype=None, value=None):
		self.name = name
		self._value = value if value else ""
		self.ctype = ctypes.STRING
		self.size = len(self._value)

	@property
	def value(self):
		return _value

	@value.setter
	def value(self, value):
		self.size = max(self.size, len(value))
		self._value = value

	def init(self, scope_name):
		return "memcpy({}.{}, {}, {});\n".format(scope_name,self.name, self.value, self.size)

	def declare(self):
		return "{} {}[{}];".format("char", var.name, var.size)

	def clone(self):
		return StringVariable(self.name, self.value)

class ObjectVariable(ScopeVariable):
	pass




class ScopeVariables:
	"""
		Defines a C structure where a scope's variables are stored.
		A object of this type takes care of declaring scope variables.

		- add : a variable
		- get : a variable
		- init/init_all : C initialization for 1/all variables and parameters
		- declare/declare_all : C declaration for 1/all variables and parameters
		- create : C struct declaration for all variables and parameters
	"""
	def __init__(self, scope):
		self.args = OrderedDict() # (name: Variable())
		self.name = scope.name
		self.scope = scope
		self.template = "struct {{{}}} {};"
		self.parameters = []

	def add(self, variable, parameter=False):
		"""
			Add a variable unique to this scope, the type is important for declaring/initializing it
		"""
		arg = self.args.get(variable.name)

		## checks if arg reassignment is correct (doesnt check if is one is array and the other is primitive - even if both have the same size)
		if arg and arg.ctype != ctypes.NONE and arg.ctype != variable.ctype:
			raise Exception("Variable with name '{}' already exists in this scope, expected {} received {}."
				.format(arg.name, arg.ctype, variable.ctype))
		
		self.args[variable.name] = variable

		if parameter:
			self.parameters.append(variable.name)

	def get(self, var_name):
		"""
			@returns 	ScopeVariable object or None
		"""
		return self.args.get(var_name)
		

	def init(self, var_name):
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

		return var.init(self.scope.name)

 
	def declare(self, var_name):
		if not self.args.has_key(var_name):
			raise Exception("Variable '{}' not in scope '{}'".format(var_name, self.name))

		var = self.args[var_name]
		
		return var.declare()

	def init_all(self):
		return '\n'.join(self.init(var) for var in self.args.keys())

	def declare_all(self):
		return '\n'.join((self.declare(var) for var in self.args.keys()))

	def create(self):
		"""
			Create the structure associated with this scope
		"""
		return self.template.format(self.declare_all(), "__" + self.name)

	def clone(self):
		## NOTE/TODO: the scope will have a repeated name, need to change it (how? find out)
		cloned = ScopeVariables(self.scope) # TODO: Do i need the scope? don't i just need a name
		cloned.parameters = list(self.parameters)
		for var in self.args.itervalues():
			cloned.add(var.clone()) 
		return cloned

	def get_params(self):
		return map(lambda p: self.args[p], self.parameters)


class ScopeFunction:
	"""
		-A object of this type takes care of initializing values from a ScopeStruct inside the function body
		- ...
	"""

	def __init__(self, scope, variables):
		self.variables = variables

		self.name = scope.name
		self.scope = scope
		#self.ret = None
		self.body = scope.body
		self.ret = None
		# add myself to the scope
		self.this_counter = scope.call_counter
		self.scope.call_counter += 1

	def name(self):
		return "{}_{}".format(self.name, self.this_counter)

	def get(self, var_name):
		return self.variables.get(var_name)
	
	def create(self):
		compilation = self.body.compile(call=True) if self.body.callable else self.body.compile()
		self.ret = self.body.type()

		fn_template = "{} {} ({}) {{{};}}"

		args = ["{} {}".format(var.ctype, var.name) for var in self.variables.get_params()]
		fnbody = "{}\n{} {}".format(self.variables.init_all(),\
			"return" if self.ret != ctypes.VOID else "",\
			compilation)

		self.scope.protos.append("{} {} ({});".format(self.ret, self.name,','.join(args)))
		
		return fn_template.format(self.ret, self.name, ','.join(args), fnbody)

	def type(self, body):
		#self.scope.function = self
		if self.ret:
			return self.ret
		 
		self.ret = body.type()
		return self.ret 

class Scope:

	def __init__(self, name="main", scope=None):

		self.name = name
		if scope:
			scope.add_scope(self)

		self.father = scope
		self.scopes = OrderedDict() # Child Scopes

		self.fullname = "{}_{}".format(scope.fullname, name) if scope else name

		self.function = None
		self.functions = []
		self.variables = ScopeVariables(self)
		
		self.fn_counter = 0
		self.helpers = []
		self.protos = []
		
		self.fn_name_template = "__fn_{scope}_{id}"
		self.fn_template = "{type} {name}(){{{body};}}"


	def add_scope(self, scope):
		"""
			add_scope - adds a new scope, as a child
						this way, from the father you can reach a scope function directly
			@arg scope 		scope object
		"""
		self.scopes[scope.name] = scope


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

		self.body = fnArgument

	def compile_protos(self):
		protos = []
		for scope in self.scopes.values():
			protos += scope.compile_protos()
		return self.protos + protos

	def helper(self, body, type=ctypes.INT):
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
		self.helpers.append(template)
		return name

	def compile(self, var):
		return "__{}.{}".format(self.name, var)

	def compile_functions(self):
		definitions = []

		for functions in self.functions:
			# NOTE: at scope creation, the list from father to children is shared, but not from scope to other_scopes
			definitions.append(functions.create())

		for scope in self.scopes.itervalues():
			definitions.extend(scope.compile_functions())	

		return self.helpers + definitions


	def compile_variables(self):
		structs = [self.variables.create()] if self.name == "main" else []

		for function in self.functions:
			structs.append(function.variables.create())# scope.compile_variables()

		for scope in self.scopes.values():
			structs.append(scope.compile_variables())

		return '\n'.join(structs)


	def new_parameter(self, name):
		"""
			Add a parameter from a function definition (DefArgument class)
	
			@name 	name to call the function parameter
		"""
		self.variables.add(ScopeVariable.create(name), parameter=True)

	def new_variable(self, name, this_type, value):
		"""
			Creates a new variable for this scope (and children) only

			@var_name	the name of the variable to be create
			@var_type 	 the type of the variable  
			@var 		 the value of the variable
		"""
		# for redeclarations of values
		old = self.variables.get(name)
		if old:
			#if variable has no type, create a new one with type
			if old.ctype == ctypes.NONE:
				self.variables[name] = ScopeVariable.create(name, ctype=this_type, value=value)

			# If using a different variable type than declared
			elif old.ctype != this_type :
				raise Exception("Can't assign {} to declared variable of type {}"
					.format(this_type, old.ctype))

		else:
			self.variables.add(ScopeVariable.create(name, ctype=this_type, value=value))

		return self.init_var(name)
			
	def get_variable(self, name):
		return self.function.get(name) if self.function else self.variables.get(name)

	def get_name(self):
		return self.function.name()


	def get_call(self, new_vars):
		for function in self.functions:
			for param in new_vars.parameters:
				if function.get(param).ctype != new_vars.get(param).ctype:
					break
			else:
				return function
		return None


	def new_call(self, variables):
		self.function = ScopeFunction(self, variables)
		self.functions.append(self.function)


	def call(self, parameters):
		"""
			Check parameters for this scope's functions
			- Gives type to all parameters without type
			- Gets function return type
			- Creates a scope for these specific parameters/return combo 
		"""	
		clone = self.variables.clone()

		for key, argument  in zip(clone.parameters, parameters):
			arg_type = argument.type()
			var = ScopeVariable.create(key, ctype=arg_type, value=key) # the value is the variable name (because it is a local parameter)
			clone.add(var)

		function = self.get_call(clone)
		if function:
			self.function = function
		else:
			self.new_call(clone)
			
		return self.function.name

	def type(self):
		return self.function.type(self.body)

