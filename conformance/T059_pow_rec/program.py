def pw(b, e):
    if e <= 0:
        return 1
    return b * pw(b, e - 1)
print(pw(2, 10))
print(pw(3, 5))
