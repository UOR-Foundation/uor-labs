# Iterator protocol implementation
# Uses stack for iterator state

iterator_init:
    PUSH 0      # current index
    PUSH 0      # collection address
    PUSH 0      # collection size
    RET

iterator_has_next:
    LOAD 0      # current index
    LOAD 2      # collection size
    SUB
    JZ has_next_false
    PUSH 1
    RET
has_next_false:
    PUSH 0
    RET

iterator_next:
    LOAD 0      # current index
    LOAD 1      # collection address
    ADD
    LOAD 0      # load value at address
    LOAD 0      # current index
    PUSH 1
    ADD
    STORE 0     # increment index
    RET
