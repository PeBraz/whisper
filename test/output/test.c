#include <stdio.h>
#include <string.h>
#include "lisp_def.c"

//prototype definitions
int __fn_main_0();
int __fn_main_1();
int __fn_main_print_hello_world_0();
void print_hello_world_0 ();
int __fn_main_hello_name_0();
void hello_name_0 (char* name);
int __fn_main_sum_up_to_n_0();
int __fn_main_sum_up_to_n_1();
int sum_up_to_n_0 (int n);
int __fn_main_sum_up_to_n_2_0();
int __fn_main_sum_up_to_n_2_1();
int sum_up_to_n_2_0 (int n);
int __fn_main_multiplication_table_0();
int __fn_main_multiplication_table_1();
int __fn_main_multiplication_table_2();
int __fn_main_multiplication_table_3();
int multiplication_table_0 ();

//variable definitions
struct {} __main;
struct {} __print_hello_world_0;
struct {char name[10];} __hello_name_0;
struct {int n;
int current;
int result;} __sum_up_to_n_0;
struct {int n;
int current;
int result;} __sum_up_to_n_2_0;
struct {int i;
int current;} __multiplication_table_0;






//function definitions
int __fn_main_0(){printf("%d\n",sum_up_to_n_0(5)
);;}
int __fn_main_1(){printf("%d\n",sum_up_to_n_2_0(5)
);;}
int __fn_main_print_hello_world_0(){printf("%s\n","Hello World!");;}
void print_hello_world_0 () {
 __fn_main_print_hello_world_0();}
int __fn_main_hello_name_0(){printf("%s\n",__hello_name_0.name);;}
void hello_name_0 (char* name) {memcpy(__hello_name_0.name, name, 10);

 __fn_main_hello_name_0();}
int __fn_main_sum_up_to_n_0(){__sum_up_to_n_0.result = (__sum_up_to_n_0.current + __sum_up_to_n_0.result);;
return __sum_up_to_n_0.current = (__sum_up_to_n_0.current + 1);;;}
int __fn_main_sum_up_to_n_1(){__sum_up_to_n_0.current = 1;;
__sum_up_to_n_0.result = 0;;
while ((__sum_up_to_n_0.current <= __sum_up_to_n_0.n)) {__fn_main_sum_up_to_n_0();};
return __sum_up_to_n_0.result;;}
int sum_up_to_n_0 (int n) {__sum_up_to_n_0.n = n;
return __fn_main_sum_up_to_n_1();}
int __fn_main_sum_up_to_n_2_0(){__sum_up_to_n_2_0.result = __if_val_int(((((__sum_up_to_n_2_0.current % 3)) == 0) || (((__sum_up_to_n_2_0.current % 5)) == 0)),(__sum_up_to_n_2_0.result + __sum_up_to_n_2_0.current),__sum_up_to_n_2_0.result);;
return __sum_up_to_n_2_0.current = (__sum_up_to_n_2_0.current + 1);;;}
int __fn_main_sum_up_to_n_2_1(){__sum_up_to_n_2_0.current = 1;;
__sum_up_to_n_2_0.result = 0;;
while ((__sum_up_to_n_2_0.current <= __sum_up_to_n_2_0.n)) {__fn_main_sum_up_to_n_2_0();};
return __sum_up_to_n_2_0.result;;}
int sum_up_to_n_2_0 (int n) {__sum_up_to_n_2_0.n = n;
return __fn_main_sum_up_to_n_2_1();}
int __fn_main_multiplication_table_0(){printf("%d %s %d %s %d\n",__multiplication_table_0.current, "x", __multiplication_table_0.i, ": ", (__multiplication_table_0.current * __multiplication_table_0.i));;}
int __fn_main_multiplication_table_1(){__fn_main_multiplication_table_0();
return __multiplication_table_0.current = (__multiplication_table_0.current + 1);;;}
int __fn_main_multiplication_table_2(){while ((__multiplication_table_0.current <= 10)) {__fn_main_multiplication_table_1();};
__multiplication_table_0.current = 0;;
return __multiplication_table_0.i = (__multiplication_table_0.i + 1);;;}
int __fn_main_multiplication_table_3(){__multiplication_table_0.i = 0;;
__multiplication_table_0.current = 0;;
while ((__multiplication_table_0.i <= 12)) {__fn_main_multiplication_table_2();};
return 0;;}
int multiplication_table_0 () {
return __fn_main_multiplication_table_3();}

int main() {
	;
;
;
;
;
print_hello_world_0()
;
hello_name_0("Alexandro")
;
__fn_main_0();
__fn_main_1();
multiplication_table_0()
;
	return 0;
}
