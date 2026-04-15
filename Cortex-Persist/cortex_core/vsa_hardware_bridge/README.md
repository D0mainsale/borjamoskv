# VSA Hardware Bridge (Law Ω0)

This directory serves as the binding layer for O(1) Vector Symbolic architectures executed purely on hardware logic (FPGA / compiled C/Rust FFI) rather than Python NumPy interpreted routines.

**Direct-Silicon JIT Enforcement:**
The Python wrappers defined here will bypass the native VM entirely for VSA collapse and Ebbinghaus decay.
