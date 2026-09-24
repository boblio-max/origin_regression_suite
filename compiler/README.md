# Layer 2: compiler tests (roadmap)

Source → bytecode/IR tests. Each test will assert on the compiled artifact
(opcode sequence / IR dump) rather than on program output, so a failure here
points at the compiler instead of the runtime.

Planned shape per test: `program.or` + `expected.opcodes` (or `expected.ir`),
checked with a small `check_compiler.py` harness.

Not started yet — Layer 1 (conformance) is the active suite.
