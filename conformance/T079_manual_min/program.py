lst = [3, 17, 9, 42, 8]
best = lst[0]
for x in lst:
    if x < best:
        best = x
print(best)
