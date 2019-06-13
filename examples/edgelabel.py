import bmt

tk = bmt.Toolkit()
b = tk.is_edgelabel('negatively regulates, process to process')

print(b)

b = tk.is_edgelabel('negatively regulates')

print(b)

b = tk.is_edgelabel('positively regulates, entity to entity')

print(b)

