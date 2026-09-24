total = 0
i = 0
while i < 20:
    i = i + 1
    if i % 2 == 0:
        continue
    total = total + i
print(total)
