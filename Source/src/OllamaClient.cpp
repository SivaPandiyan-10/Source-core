#include "OllamaClient.h"
#include <curl/curl.h>
#include <string>
#include <sstream>
#include <iostream>

static size_t write_cb(void *ptr, size_t size, size_t nmemb, void *userdata) {
    std::string *s = reinterpret_cast<std::string*>(userdata);
    s->append(reinterpret_cast<char*>(ptr), size * nmemb);
    return size * nmemb;
}

OllamaClient::OllamaClient(const std::string &url) : url_(url) {}
OllamaClient::~OllamaClient() = default;

std::string OllamaClient::generate(const std::string &prompt) {
    std::string out;
    CURL *c = curl_easy_init();
    if (!c) return "";
    std::string endpoint = url_ + "/api/generate";
    std::string body = "{\"prompt\": \"" + prompt + "\"}";
    struct curl_slist *headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    curl_easy_setopt(c, CURLOPT_URL, endpoint.c_str());
    curl_easy_setopt(c, CURLOPT_POSTFIELDS, body.c_str());
    curl_easy_setopt(c, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(c, CURLOPT_WRITEFUNCTION, write_cb);
    curl_easy_setopt(c, CURLOPT_WRITEDATA, &out);
    CURLcode rc = curl_easy_perform(c);
    curl_slist_free_all(headers);
    curl_easy_cleanup(c);
    if (rc != CURLE_OK) return string("(ollama error)");
    return out;
}
