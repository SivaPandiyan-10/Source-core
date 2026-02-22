#include "EncryptionUtil.h"
#include <string>
#include <cstdlib>
#include <vector>
#include <sstream>

#if defined(__has_include)
#  if __has_include(<sodium.h>)
#    include <sodium.h>
#    define HAVE_SODIUM 1
#  endif
#endif

static std::string to_hex(const std::vector<unsigned char> &bin) {
    std::ostringstream ss;
    ss<<std::hex;
    for (unsigned char c: bin) ss << (int)((c>>4)&0xF) << (int)(c&0xF);
    return ss.str();
}

static std::vector<unsigned char> from_hex(const std::string &hex) {
    std::vector<unsigned char> out;
    out.reserve(hex.size()/2);
    for (size_t i=0;i+1<hex.size(); i+=2) {
        unsigned int hi = 0; unsigned int lo = 0;
        auto cv = [](char c)->int { if (c>='0'&&c<='9') return c-'0'; if (c>='a'&&c<='f') return 10 + c-'a'; if (c>='A'&&c<='F') return 10 + c-'A'; return 0; };
        hi = cv(hex[i]); lo = cv(hex[i+1]);
        out.push_back((unsigned char)((hi<<4) | lo));
    }
    return out;
}

namespace EncryptionUtil {

std::string getKey() {
    const char *k = std::getenv("PERSONAL_AI_KEY");
    if (!k) return "default_demo_key_please_change";
    return std::string(k);
}

std::string encrypt(const std::string &plaintext) {
#ifdef HAVE_SODIUM
    if (sodium_init() < 0) {
        // fallback
    } else {
        std::string keyraw = getKey();
        unsigned char key[crypto_secretbox_KEYBYTES];
        crypto_generichash(key, sizeof(key), (const unsigned char*)keyraw.data(), keyraw.size(), NULL, 0);
        std::vector<unsigned char> nonce(crypto_secretbox_NONCEBYTES);
        randombytes_buf(nonce.data(), nonce.size());
        std::vector<unsigned char> cipher(plaintext.size() + crypto_secretbox_MACBYTES);
        crypto_secretbox_easy(cipher.data(), (const unsigned char*)plaintext.data(), plaintext.size(), nonce.data(), key);
        // store nonce + cipher as hex
        std::vector<unsigned char> combined;
        combined.insert(combined.end(), nonce.begin(), nonce.end());
        combined.insert(combined.end(), cipher.begin(), cipher.end());
        return to_hex(combined);
    }
#endif
    // Fallback XOR (demo only)
    std::string key = getKey();
    std::string out = plaintext;
    for (size_t i = 0; i < out.size(); ++i) out[i] ^= key[i % key.size()];
    return out;
}

std::string decrypt(const std::string &ciphertext) {
#ifdef HAVE_SODIUM
    if (sodium_init() >= 0) {
        auto bin = from_hex(ciphertext);
        if (bin.size() >= crypto_secretbox_NONCEBYTES + crypto_secretbox_MACBYTES) {
            std::string keyraw = getKey();
            unsigned char key[crypto_secretbox_KEYBYTES];
            crypto_generichash(key, sizeof(key), (const unsigned char*)keyraw.data(), keyraw.size(), NULL, 0);
            const unsigned char *nonce = bin.data();
            const unsigned char *cptr = bin.data() + crypto_secretbox_NONCEBYTES;
            size_t clen = bin.size() - crypto_secretbox_NONCEBYTES;
            std::vector<unsigned char> out(clen - crypto_secretbox_MACBYTES);
            if (crypto_secretbox_open_easy(out.data(), cptr, clen, nonce, key) == 0) {
                return std::string((char*)out.data(), out.size());
            }
        }
    }
#endif
    // XOR fallback
    std::string key = getKey();
    std::string out = ciphertext;
    for (size_t i = 0; i < out.size(); ++i) out[i] ^= key[i % key.size()];
    return out;
}


}
