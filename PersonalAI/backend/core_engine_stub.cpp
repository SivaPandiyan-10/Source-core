#include <iostream>
#include <memory>
#include <string>

#include <grpcpp/grpcpp.h>
#include "core_engine.grpc.pb.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;

class CoreEngineServiceImpl final : public core::CoreEngine::Service {
  Status CalculateFinancialModel(ServerContext* context, const core::CalcRequest* req,
                                 core::CalcResponse* resp) override {
    // Placeholder: call into high-performance finance library here
    resp->set_output_json("{\"result\": 0}");
    resp->set_compute_time(0.0);
    return Status::OK;
  }

  Status EncryptBlob(ServerContext* context, const core::EncryptRequest* req,
                     core::EncryptResponse* resp) override {
    // Placeholder: perform encryption with key management
    resp->set_ciphertext(req->plaintext());
    resp->set_key_id(req->key_id());
    return Status::OK;
  }

  Status DecryptBlob(ServerContext* context, const core::DecryptRequest* req,
                     core::DecryptResponse* resp) override {
    // Placeholder: perform decryption
    resp->set_plaintext(req->ciphertext());
    return Status::OK;
  }

  Status StoreRecord(ServerContext* context, const core::StoreRequest* req,
                     core::StoreResponse* resp) override {
    // Placeholder: store record in DB and return id
    resp->set_ok(true);
    resp->set_id("stub-id");
    return Status::OK;
  }
};

void RunServer(const std::string& server_address) {
  CoreEngineServiceImpl service;

  ServerBuilder builder;
  builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
  builder.RegisterService(&service);
  std::unique_ptr<Server> server(builder.BuildAndStart());
  std::cout << "CoreEngine server listening on " << server_address << std::endl;
  server->Wait();
}

int main(int argc, char** argv) {
  std::string addr = "0.0.0.0:50051";
  RunServer(addr);
  return 0;
}
