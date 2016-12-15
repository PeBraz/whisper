

#define __if_val(type)\
	type __if_val_ ## type (int cond, type __arg1, type __arg2)\
	{\
		if (cond) {\
			return __arg1;\
		} else {\
			return __arg2;\
		}\
	}\

#define __if_ref(type)\
	type *__if_ref_ ## type (int cond, type *__arg1, type *__arg2)\
	{\
		if (cond) {\
			return __arg1;\
		} else {\
			return __arg2;\
		}\
	}\

#define __if_val_fn(type)\
	type __if_val_fn_ ## type (int cond, type (*__fn1)(), type (*__fn2)())\
	{\
		if (cond) {\
			return __fn1();\
		} else {\
			return __fn2();\
		}\
	}\

#define __if_ref_fn(type)\
	type * __if_ref_fn_ ## type (int cond, type *(*__fn1)(), type *(*__fn2)())\
	{\
		if (cond) {\
			return __fn1();\
		} else {\
			return __fn2();\
		}\
	}\


int __if_val_fn_void(int cond, int(*__fn1)(), int(*__fn2)()) 
{
	if (cond)
		__fn1();
	else
		__fn2();
	return 0;
}




char *__reads()
{
	static char buffer[1024];
	fgets(buffer, 1024, stdin);
	size_t s = strlen(buffer);
	if (buffer[s] == '\n')
		buffer[s] = '\0'; 
	return buffer;
}


__if_val(int);
__if_val(char);
__if_ref(char);
__if_ref(int);
__if_val_fn(int);
__if_val_fn(char);
__if_ref_fn(int);
__if_ref_fn(char);
