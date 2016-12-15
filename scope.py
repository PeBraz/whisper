from collections import OrderedDict

from wptypes import ctypes

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
		elif ctype == ctypes.NONE:
			return 						#This is a parameter for which I don't know the type yet
		else:
			raise Exception("Don't know what to assign as initial value to the type received\n"
				" variable {{\n"
				"\twhisper name (identifier): {}\n"
				"\tc name (name): {}\n}}".format(self.identifier, self.name))
    
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
			Add a variable unique to this scope, the type is important for declaring/initializing it
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

		self.in_compilation_scope = self

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

	def new_parameter(self, parameter_name):
		self.scope_struct.add_variable(ScopeVariable(parameter_name, ctypes.NONE))
		self.scope_function.add_arg(parameter_name, ctypes.NONE)

	def new_variable(self, var_name, var_type, var):
		"""
			Creates a new variable for this scope (and children) only

			@var_name	the name of the variable to be create
			@var_type 	(optional) the type of the variable  
			@var 		(optional) the value of the variable
		"""

		"""
		# for local variables, for which the type is not known
		if not var_type: 
			print "WTFDAFGWFG"
			#print var_name, "->",var
			self.scope_struct.add_variable(ScopeVariable(var_name, ctypes.NONE, value=var))
			self.scope_function.add_arg(var_name, ctypes.NONE)
			return 
		"""

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
		structs = [self.scope_struct.create()] if self.name == "main" else []

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

