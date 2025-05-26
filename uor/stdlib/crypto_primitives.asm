# Cryptographic VM primitives

# SHA-256 hash
crypto_sha256:
    LOAD 0      # data address
    LOAD 1      # size
    HASH
    RET

# Digital signature
crypto_sign:
    LOAD 0      # data
    LOAD 1      # private key
    SIGN
    RET

crypto_verify:
    LOAD 0      # data
    LOAD 1      # signature
    LOAD 2      # public key
    VERIFY
    RET

# Random number generation for keys
crypto_random:
    RNG
    RET

# AES encryption (simplified)
aes_encrypt:
    PUSH 30     # AES encrypt syscall
    LOAD 0      # plaintext
    LOAD 1      # key
    LOAD 2      # size
    SYSCALL
    RET

aes_decrypt:
    PUSH 31     # AES decrypt syscall
    LOAD 0      # ciphertext
    LOAD 1      # key
    LOAD 2      # size
    SYSCALL
    RET

# Key derivation
derive_private_key:
    LOAD 0      # seed
    PUSH 123456789
    MUL
    HASH
    RET

derive_public_key:
    LOAD 0      # private key
    PUSH 65537  # public exponent
    MUL
    HASH
    RET
