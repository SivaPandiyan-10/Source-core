#pragma once
#include <string>

namespace EncryptionUtil {
    // Returns a secret key (from env or default). Implementation may use libsodium.
    std::string getKey();
    // Encrypt plaintext; returns encoded ciphertext safe to store in DB.
    std::string encrypt(const std::string &plaintext);
    // Decrypt encoded ciphertext back to plaintext.
    std::string decrypt(const std::string &ciphertext);
}
