

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

