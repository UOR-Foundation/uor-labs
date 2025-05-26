# Memory management helpers

# Allocate memory with coherence tracking
allocate:
    LOAD 0      # size
    ALLOC
    # Add coherence metadata
    PUSH 1      # coherence flag
    STORE 0
    RET

# Free memory with coherence cleanup
free:
    LOAD 0      # address
    # Clear coherence metadata
    PUSH 0
    STORE 0
    FREE
    RET

# Memory copy
memcpy:
    LOAD 0      # destination
    LOAD 1      # source
    LOAD 2      # size
copy_loop:
    LOAD 2      # size
    JZ copy_done
    LOAD 1      # source
    LOAD 0      # value at source
    LOAD 0      # destination
    STORE 0     # store value
    # Increment pointers
    LOAD 0
    PUSH 1
    ADD
    STORE 0
    LOAD 1
    PUSH 1
    ADD
    STORE 1
    LOAD 2
    PUSH 1
    SUB
    STORE 2
    JMP copy_loop
copy_done:
    RET

# Memory compare
memcmp:
    LOAD 0      # addr1
    LOAD 1      # addr2
    LOAD 2      # size
cmp_loop:
    LOAD 2
    JZ cmp_equal
    LOAD 0
    LOAD 0      # value1
    LOAD 1
    LOAD 0      # value2
    SUB
    JNZ cmp_done
    # Increment pointers
    LOAD 0
    PUSH 1
    ADD
    STORE 0
    LOAD 1
    PUSH 1
    ADD
    STORE 1
    LOAD 2
    PUSH 1
    SUB
    STORE 2
    JMP cmp_loop
cmp_equal:
    PUSH 0
    RET
cmp_done:
    RET
