import dis
import timeit

# Version 1: Nested list comprehension with inner 'if'
def comprehension_version():
    return [x * y for x in range(100) for y in range(100) if y % 10 == 0]

# Version 2: Equivalent nested for-loops with if statement
def loop_version():
    result = []
    for x in range(100):
        for y in range(100):
            if y % 10 == 0:
                result.append(x * y)
    return result

# Disassemble both versions to inspect bytecode
print("Bytecode: comprehension_version")
dis.dis(comprehension_version)

print("\nBytecode: loop_version")
dis.dis(loop_version)

# Time execution of both functions
print("\nTiming comprehension_version:")
print(timeit.timeit('comprehension_version()', globals=globals(), number=10000))

print("Timing loop_version:")
print(timeit.timeit('loop_version()', globals=globals(), number=10000))
