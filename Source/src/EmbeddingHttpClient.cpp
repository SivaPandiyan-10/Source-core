#include "EmbeddingHttpClient.h"
#include <curl/curl.h>
#include <iostream>
static size_t write_cb(void *ptr, size_t size, size_t nmemb, void *userdata) {
    std::string *s = reinterpret_cast<std::string*>(userdata);
    s->append(reinterpret_cast<char*>(ptr), size * nmemb);
    return size * nmemb;
}

EmbeddingHttpClient::EmbeddingHttpClient(const std::string &url) : url_(url) {}
EmbeddingHttpClient::~EmbeddingHttpClient() = default;

// very small ad-hoc JSON parsing for {"embedding": [x, y, z]}
static std::vector<float> parseEmbeddingFromJson(const std::string &s) {
    std::vector<float> out;
    auto pos = s.find("[");
    if (pos == std::string::npos) return out;
    auto end = s.find("]", pos);
    if (end == std::string::npos) return out;
    std::string inner = s.substr(pos + 1, end - pos - 1);
    std::istringstream is(inner);
    std::string tok;
    while (std::getline(is, tok, ',')) {
        try {
            out.push_back(std::stof(tok));
        } catch (...) { }
    }
    return out;
}

std::vector<float> EmbeddingHttpClient::embed(const std::string &text) {
    std::vector<float> out;
    CURL *c = curl_easy_init();
    if (!c) return out;
    std::string body = "{\"text\": \"" + text + "\"}";
    std::string resp;
    struct curl_slist *headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    curl_easy_setopt(c, CURLOPT_URL, url_.c_str());
    curl_easy_setopt(c, CURLOPT_POSTFIELDS, body.c_str());
    curl_easy_setopt(c, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(c, CURLOPT_WRITEFUNCTION, write_cb);
    curl_easy_setopt(c, CURLOPT_WRITEDATA, &resp);
    CURLcode rc = curl_easy_perform(c);
    curl_slist_free_all(headers);
    curl_easy_cleanup(c);
    if (rc != CURLE_OK) return out;
    out = parseEmbeddingFromJson(resp);
    return out;
}
