// Communications
#ifndef COMMUNICATION_HPP
#define COMMUNICATION_HPP

#include "base.hpp"
#include <queue>
#include <mutex>
#include <thread>

// Serial communication (Pi <-> Teensy)
class SerialInterface : public ICommunicationInterface {
private:
    std::string portName_;
    int baudRate_;
    bool connected_;
    std::queue<std::vector<uint8_t>> txQueue_;
    std::queue<std::vector<uint8_t>> rxQueue_;
    std::mutex txMutex_;
    std::mutex rxMutex_;

public:
    SerialInterface(const std::string& port, int baud)
        : portName_(port), baudRate_(baud), connected_(false) {}

    bool initialize() override {
        // Open serial port
        connected_ = true; // Placeholder
        return connected_;
    }

    bool update() override {
        // Process queues
        return connected_;
    }

    bool shutdown() override {
        connected_ = false;
        return true;
    }

    bool send(const std::vector<uint8_t>& data) override {
        if (!connected_) return false;
        std::lock_guard<std::mutex> lock(txMutex_);
        txQueue_.push(data);
        return true;
    }

    std::vector<uint8_t> receive() override {
        std::lock_guard<std::mutex> lock(rxMutex_);
        if (rxQueue_.empty()) return {};
        auto data = rxQueue_.front();
        rxQueue_.pop();
        return data;
    }

    bool isConnected() const override { return connected_; }
    
    std::string getStatus() const override {
        return "Serial " + portName_ + ": " + 
               (connected_ ? "Connected" : "Disconnected");
    }
    
    std::string getComponentName() const override { 
        return "Serial_" + portName_; 
    }
};

// Modbus communication for industrial equipment
class ModbusInterface : public ICommunicationInterface {
private:
    std::string deviceAddress_;
    bool connected_;

public:
    ModbusInterface(const std::string& address)
        : deviceAddress_(address), connected_(false) {}

    bool initialize() override {
        // Initialize Modbus connection
        connected_ = true;
        return true;
    }

    bool update() override { return connected_; }
    bool shutdown() override { connected_ = false; return true; }

    bool send(const std::vector<uint8_t>& data) override {
        // Send Modbus command
        return connected_;
    }

    std::vector<uint8_t> receive() override {
        // Receive Modbus response
        return {};
    }

    bool isConnected() const override { return connected_; }
    
    std::string getStatus() const override {
        return "Modbus " + deviceAddress_ + ": " + 
               (connected_ ? "Connected" : "Disconnected");
    }
    
    std::string getComponentName() const override { 
        return "Modbus_" + deviceAddress_; 
    }
};

// Telemetry uplink (Pi -> Surface)
class TelemetryUplink : public ICommunicationInterface {
private:
    std::string surfaceIP_;
    int port_;
    bool connected_;

public:
    TelemetryUplink(const std::string& ip, int port)
        : surfaceIP_(ip), port_(port), connected_(false) {}

    bool initialize() override {
        // Establish network connection
        connected_ = true;
        return true;
    }

    bool update() override { return connected_; }
    bool shutdown() override { connected_ = false; return true; }

    bool send(const std::vector<uint8_t>& data) override {
        // Send telemetry packet
        return connected_;
    }

    std::vector<uint8_t> receive() override {
        // Receive commands from surface
        return {};
    }

    bool isConnected() const override { return connected_; }
    
    std::string getStatus() const override {
        return "Telemetry " + surfaceIP_ + ":" + std::to_string(port_) + 
               " - " + (connected_ ? "Connected" : "Disconnected");
    }
    
    std::string getComponentName() const override { return "TelemetryLink"; }
};

#endif