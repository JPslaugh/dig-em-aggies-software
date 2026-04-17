// DataLogger
#ifndef DATA_LOGGER_HPP
#define DATA_LOGGER_HPP

#include "base.hpp"
#include <fstream>
#include <sstream>
#include <iomanip>
#include <chrono>

class DataLogger : public ISystemComponent {
private:
    std::ofstream logFile_;
    std::string filename_;
    bool isLogging_;
    
    std::string getTimestamp() {
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()) % 1000;
        
        std::stringstream ss;
        ss << std::put_time(std::localtime(&time), "%Y-%m-%d %H:%M:%S");
        ss << '.' << std::setfill('0') << std::setw(3) << ms.count();
        return ss.str();
    }

public:
    DataLogger(const std::string& filename) 
        : filename_(filename), isLogging_(false) {}

    bool initialize() override {
        logFile_.open(filename_, std::ios::app);
        if (!logFile_.is_open()) return false;
        
        isLogging_ = true;
        logFile_ << "\n=== Session Started: " << getTimestamp() << " ===\n";
        return true;
    }
    // Roombaaaaaa
    bool update() override {
        return isLogging_;
    }

    bool shutdown() override {
        if (logFile_.is_open()) {
            logFile_ << "=== Session Ended: " << getTimestamp() << " ===\n";
            logFile_.close();
        }
        isLogging_ = false;
        return true;
    }

    void log(const std::string& message) {
        if (!isLogging_) return;
        logFile_ << getTimestamp() << " | " << message << std::endl;
    }

    void logComponentStatus(const ISystemComponent& component) {
        log(component.getComponentName() + ": " + component.getStatus());
    }

    std::string getStatus() const override {
        return isLogging_ ? "Logging to " + filename_ : "Not logging";
    }

    std::string getComponentName() const override { return "DataLogger"; }
};

#endif