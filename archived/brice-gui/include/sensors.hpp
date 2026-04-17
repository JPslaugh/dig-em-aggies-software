// Sensors
#ifndef SENSORS_HPP
#define SENSORS_HPP

#include "base.hpp"
#include <deque>
#include <algorithm>
#include <numeric>

// Concrete sensor implementations
class PressureSensor : public ISensor {
private:
    std::string name_;
    double currentValue_;
    double calibrationOffset_;
    bool healthy_;
    std::deque<double> historyBuffer_;
    static constexpr size_t BUFFER_SIZE = 10;

public:
    PressureSensor(const std::string& name) 
        : name_(name), currentValue_(0.0), 
          calibrationOffset_(0.0), healthy_(false) {}

    bool initialize() override {
        healthy_ = true;
        return true;
    }

    bool update() override {
        // Read from hardware (placeholder)
        // In real implementation, read from ADC/I2C
        return healthy_;
    }

    bool shutdown() override {
        healthy_ = false;
        return true;
    }

    double readValue() override {
        if (historyBuffer_.size() >= BUFFER_SIZE) {
            historyBuffer_.pop_front();
        }
        historyBuffer_.push_back(currentValue_ + calibrationOffset_);
        
        // Return filtered value (moving average)
        return std::accumulate(historyBuffer_.begin(), 
                              historyBuffer_.end(), 0.0) / historyBuffer_.size();
    }

    bool calibrate() override {
        calibrationOffset_ = -currentValue_;
        return true;
    }

    bool isHealthy() const override { return healthy_; }
    std::string getUnits() const override { return "PSI"; }
    std::string getStatus() const override { 
        return name_ + ": " + std::to_string(currentValue_) + " " + getUnits();
    }
    std::string getComponentName() const override { return name_; }
};

class TemperatureSensor : public ISensor {
private:
    std::string name_;
    double currentValue_;
    bool healthy_;

public:
    TemperatureSensor(const std::string& name) 
        : name_(name), currentValue_(0.0), healthy_(false) {}

    bool initialize() override { healthy_ = true; return true; }
    bool update() override { return healthy_; }
    bool shutdown() override { healthy_ = false; return true; }
    double readValue() override { return currentValue_; }
    bool calibrate() override { return true; }
    bool isHealthy() const override { return healthy_; }
    std::string getUnits() const override { return "°C"; }
    std::string getStatus() const override { 
        return name_ + ": " + std::to_string(currentValue_) + " " + getUnits();
    }
    std::string getComponentName() const override { return name_; }
};

class IMUSensor : public ISensor {
private:
    std::string name_;
    struct IMUData {
        double roll, pitch, yaw;
        double accelX, accelY, accelZ;
    } data_;
    bool healthy_;

public:
    IMUSensor(const std::string& name) 
        : name_(name), healthy_(false) {
        data_ = {0, 0, 0, 0, 0, 0};
    }

    bool initialize() override { healthy_ = true; return true; }
    bool update() override { return healthy_; }
    bool shutdown() override { healthy_ = false; return true; }
    double readValue() override { return data_.yaw; } // Return primary value
    bool calibrate() override { return true; }
    bool isHealthy() const override { return healthy_; }
    std::string getUnits() const override { return "degrees"; }
    std::string getStatus() const override { 
        return name_ + ": R=" + std::to_string(data_.roll) + 
               " P=" + std::to_string(data_.pitch) + 
               " Y=" + std::to_string(data_.yaw);
    }
    std::string getComponentName() const override { return name_; }
    
    IMUData getData() const { return data_; }
};

#endif