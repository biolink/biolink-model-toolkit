import bmt

tk = bmt.Toolkit()
b = tk.is_predicate('process negatively regulates process')

print(b)

b = tk.is_predicate('negatively regulates')

print(b)

b = tk.is_predicate('entity positively regulates entity')

print(b)

