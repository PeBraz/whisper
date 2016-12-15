from collections import namedtuple

CType = namedtuple('CType', ['STRING', 'INT', 'VOID', 'NONE'])
ctypes = CType(
	NONE=0,
	STRING="char*",
	INT="int",
	VOID="void"
)

