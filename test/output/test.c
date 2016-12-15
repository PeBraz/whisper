#include <stdio.h>
#include <string.h>
#include "lisp_def.c"

//prototype definitions
int __fn_main_0();
int __fn_main_sum_up_to_n_0();
int __fn_main_sum_up_to_n_1();
int sum_up_to_n_0 (int n);

//variable definitions
struct {} __main;


struct {int n;
int current;
int result;} __sum_up_to_n_0;


//function definitions
int __fn_main_0(){printf("%d\n",sum_up_to_n_0(2)
);;}
int __fn_main_sum_up_to_n_0(){__sum_up_to_n_0.result = (__sum_up_to_n_0.current + __sum_up_to_n_0.result);;
return __sum_up_to_n_0.current = (__sum_up_to_n_0.current + 1);;;}
int __fn_main_sum_up_to_n_1(){__sum_up_to_n_0.current = 1;;
__sum_up_to_n_0.result = 0;;
while ((__sum_up_to_n_0.current <= __sum_up_to_n_0.n)) {__fn_main_sum_up_to_n_0();};
return __sum_up_to_n_0.result;;}
int sum_up_to_n_0 (int n) {__sum_up_to_n_0.n = n;
return __fn_main_sum_up_to_n_1();}

int main() {
	;
;
;
__fn_main_0();
	return 0;
}
